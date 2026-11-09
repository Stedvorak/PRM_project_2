"""Validate original real sessions and explicitly decimate 50Hz to 25Hz.

Original CSV/metadata bytes are never rewritten. Collection-round grouping is
defined before windowing; adjacent follow-up takes stay in the same round.
"""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

STATES = ('calm', 'fast', 'unattached', 'shaking')
COLUMNS = ('t_ms', 'ax_g', 'ay_g', 'az_g', 'gx_dps', 'gy_dps', 'gz_dps')


def prepare(raw=Path('data/raw'), destination=Path('data/validated'),
            report_dir=Path('outputs/verification/V07_all_sessions')):
    if destination.exists() or report_dir.exists():
        raise FileExistsError('Dataset/report output already exists; never overwrite')
    files = sorted(raw.glob('*.csv'))
    if set(p.stem for p in files) != set(p.stem for p in raw.glob('*.json')):
        raise ValueError('Every CSV must have exactly one metadata JSON')
    records, hashes = [], set()
    for path in files:
        metadata_path = path.with_suffix('.json')
        meta = json.loads(metadata_path.read_text(encoding='utf-8-sig'))
        with path.open(newline='', encoding='utf-8-sig') as stream:
            reader = csv.reader(stream)
            if next(reader) != list(COLUMNS):
                raise ValueError(f'Incorrect columns: {path}')
            rows = list(reader)
        if not rows or any(len(r) != 7 or any(not x.strip() for x in r) for r in rows):
            raise ValueError(f'Missing/malformed fields: {path}')
        a = np.asarray(rows, dtype=np.float64)
        if not np.isfinite(a).all():
            raise ValueError(f'Nonfinite values: {path}')
        times, gaps = a[:, 0], np.diff(a[:, 0])
        if (times < 0).any() or (times != np.floor(times)).any() or (gaps <= 0).any():
            raise ValueError(f'Invalid timestamps: {path}')
        rate = 1000 * len(gaps) / (times[-1] - times[0])
        missing = int(np.maximum(0, np.floor(gaps / 20 + .5).astype(int) - 1).sum())
        units = {'t_ms': 'ms since ESP32 boot', **{k: 'g' for k in COLUMNS[1:4]},
                 **{k: 'deg/s' for k in COLUMNS[4:]}}
        label = meta.get('label')
        if (label not in STATES or meta.get('source') != 'real_sensor' or
            meta.get('csv_file') != path.name or meta.get('recording_id') != path.stem or
            meta.get('units') != units or meta.get('sample_rate_hz') != 50 or
            meta.get('valid_samples') != len(rows) or not meta.get('complete') or
            meta.get('error') is not None or meta.get('first_t_ms') != int(times[0]) or
            meta.get('last_t_ms') != int(times[-1]) or
            abs(meta.get('observed_sample_rate_hz', 0) - rate) > 1e-8 or
            meta.get('estimated_missing_samples') != missing or
            not 49 <= rate <= 51 or gaps.max() > 40 or not 1400 <= len(rows) <= 1600):
            raise ValueError(f'Metadata/quality mismatch: {path}')
        # Nominal +/-250deg/s permits signed ADC rails of32768/131 deg/s.
        if (np.abs(a[:, 1:4]) > 32768 / 16384 + 1e-6).any() or (
                np.abs(a[:, 4:]) > 32768 / 131 + 1e-5).any():
            raise ValueError(f'Values outside sensor representation: {path}')
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in hashes:
            raise ValueError(f'Duplicate content: {path}')
        hashes.add(digest)
        records.append({'recording_id': path.stem, 'state': label, 'raw_path': path.as_posix(),
            'metadata_path': metadata_path.as_posix(), 'sha256': digest,
            'metadata_sha256': hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
            'samples': len(rows), 'first_t_ms': int(times[0]), 'last_t_ms': int(times[-1]),
            'observed_rate_hz': float(rate), 'min_interval_ms': int(gaps.min()),
            'max_interval_ms': int(gaps.max()), 'estimated_missing_samples': missing,
            'malformed_serial_lines_rejected': meta['malformed_records_rejected'],
            'accel_near_rail_rows': int((np.abs(a[:, 1:4]) >= 1.999).any(axis=1).sum()),
            'gyro_near_rail_rows': int((np.abs(a[:, 4:]) >= 249.9).any(axis=1).sum()),
            '_rows': rows})
    by_class = {s: sorted([r for r in records if r['state'] == s],
                         key=lambda r: r['first_t_ms']) for s in STATES}
    if any(len(items) < 2 for items in by_class.values()):
        raise ValueError('At least two separated recordings/class required')
    ordered = sorted(records, key=lambda r: r['first_t_ms'])
    if any(a['last_t_ms'] >= b['first_t_ms'] for a, b in zip(ordered, ordered[1:])):
        raise ValueError('Overlapping boot timestamps; inspect sessions/boots manually')
    for label, items in by_class.items():
        for index, item in enumerate(items):
            item['group_id'] = 'R1_initial' if index == 0 else 'R2_followup'
    r1_end = max(r['last_t_ms'] for r in records if r['group_id'] == 'R1_initial')
    r2_start = min(r['first_t_ms'] for r in records if r['group_id'] == 'R2_followup')
    if r1_end >= r2_start:
        raise ValueError('Inferred collection rounds are not temporally separated')
    destination.mkdir(parents=True, exist_ok=False)
    manifest_records = []
    for record in records:
        # Hardware DLPF5=10Hz was used during recording, below25Hz Nyquist.
        # Keep original text values/timestamps at indices0,2,4...; no interpolation.
        rows = record.pop('_rows')
        derived = destination / (record['recording_id'] + '_25hz.csv')
        with derived.open('x', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream, lineterminator='\n')
            writer.writerow(COLUMNS)
            writer.writerows(rows[::2])
        record['derived_samples'] = len(rows[::2])
        manifest_records.append({'recording_id': record['recording_id'],
            'state': record['state'], 'group_id': record['group_id'], 'path': derived.name,
            'raw_path': record['raw_path'], 'raw_sha256': record['sha256']})
    policy = ('Two inferred whole collection rounds: first take/class versus all later '
              'takes/class. Adjacent follow-up takes share a group. One device/boot; '
              'independent people or physical experimental sessions are not established.')
    manifest = {'source': 'real_sensor', 'sample_rate_hz': 25, 'raw_sample_rate_hz': 50,
        'preprocessing': 'DLPF5=10Hz in sensor; deterministic keep-every-second sample; '
                         'original timestamps/values retained; originals unchanged',
        'group_policy': policy, 'recordings': manifest_records}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    summary = {}
    for label, items in by_class.items():
        bouts = 1 + sum(b['first_t_ms'] - a['last_t_ms'] > 1000
                        for a, b in zip(items, items[1:]))
        summary[label] = {'recordings': len(items), 'raw_samples': sum(r['samples'] for r in items),
                          'separated_acquisition_bouts': bouts}
    report_dir.mkdir(parents=True, exist_ok=False)
    report = {'validation': 'PASS', 'group_policy': policy, 'classes': summary,
              'total_raw_samples': sum(r['samples'] for r in records), 'recordings': records,
              'provenance_limit': 'Real source and physical labels rely on operator collection; '
                                  'uniqueness/metadata checks cannot independently prove ground truth.'}
    (report_dir / 'validation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))
    print('Validated originals unchanged; derived25Hz manifest:', destination / 'manifest.json')


if __name__ == '__main__':
    prepare()
