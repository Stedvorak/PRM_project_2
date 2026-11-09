"""M05/M06: same grouped validation using orientation-invariant feature channels."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

try:
    from tools.compare_models import grouped_dataset, group_folds, score, export_model, model_description
    from tools.train_model import STATES, FEATURE_NAMES, git_commit
except ModuleNotFoundError:
    from compare_models import grouped_dataset, group_folds, score, export_model, model_description
    from train_model import STATES, FEATURE_NAMES, git_commit


PARAMS = {
    "M05": {"name": "invariant_decision_tree_depth5", "kind": "tree", "max_depth": 5,
            "min_samples_leaf": 2, "class_weight": "balanced", "random_state": 42},
    "M06": {"name": "invariant_random_forest_8_depth4", "kind": "forest", "n_estimators": 8,
            "max_depth": 4, "min_samples_leaf": 2, "class_weight": "balanced", "random_state": 42},
}


def estimator(method):
    p=dict(PARAMS[method]);p.pop("name");kind=p.pop("kind")
    return DecisionTreeClassifier(**p) if kind=="tree" else RandomForestClassifier(**p,n_jobs=1)


def compare(manifest_path=Path("data/validated/manifest.json"), output_root=Path("outputs/results"),
            summary_root=Path("outputs/comparison/C02_invariant_v1")):
    destinations={mid:output_root/f"{mid}_v1" for mid in PARAMS}
    if summary_root.exists() or any(path.exists() for path in destinations.values()):
        raise FileExistsError("Refusing to overwrite invariant experiments")
    records,original,y,recording_ids,groups=grouped_dataset(manifest_path,25)
    x=original.copy()
    x[:,:6]=0  # Preserve12-feature firmware ABI; no orientation-sensitive axis statistics.
    strategy,folds=group_folds(y,groups)
    results=[]
    for method,params in PARAMS.items():
        probabilities=np.full((len(y),4),np.nan)
        fold_ids=np.full(len(y),-1,dtype=int)
        fold_metrics=[]
        for fold in folds:
            train,test=fold["train"],fold["test"]
            model=estimator(method).fit(x[train],y[train])
            p=model.predict_proba(x[test])
            probabilities[test]=p;fold_ids[test]=fold["fold"]
            fold_metrics.append({"fold":fold["fold"],"train_groups":fold["train_groups"],
                "test_groups":fold["test_groups"],"train_windows":len(train),"test_windows":len(test),
                **score(y[test],np.argmax(p,axis=1))})
        assert np.isfinite(probabilities).all() and np.all(fold_ids>=0)
        final=estimator(method).fit(x,y)
        trees=[final] if isinstance(final,DecisionTreeClassifier) else final.estimators_
        assert all(np.all(tree.tree_.feature[tree.tree_.feature>=0]>=6) for tree in trees)
        # Raw and masked inputs must be identical for the final candidate because
        # no split may use the six constant training columns.
        np.testing.assert_array_equal(final.predict_proba(original),final.predict_proba(x))
        header=export_model(final,method,"1")
        pooled=score(y,np.argmax(probabilities,axis=1))
        metrics={"method_id":method,"version":"1","name":params["name"],"source":"real_sensor",
            "evaluated_at_utc":datetime.now(timezone.utc).isoformat(),"code_commit":git_commit(),
            "manifest_sha256":hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "parameters":{**params,"training_masked_columns":list(range(6)),"used_feature_columns":list(range(6,12))},
            "sample_rate_hz":25,"window_samples":100,"stride_samples":25,
            "feature_names":list(FEATURE_NAMES),"states":list(STATES),"validation_strategy":strategy,
            "folds":fold_metrics,"pooled_grouped_heldout":pooled,
            "mean_fold_balanced_accuracy":float(np.mean([f["balanced_accuracy"] for f in fold_metrics])),
            "fold_balanced_accuracy_std":float(np.std([f["balanced_accuracy"] for f in fold_metrics])),
            "windows":len(y),"recordings":len(records),"groups":len(set(groups)),
            "recording_groups":[{"recording_id":r["recording_id"],"group_id":r["group_id"],
                                  "state":r["state"],"sha256":r["sha256"]} for r in records],
            "export_header_bytes":len(header.encode("utf-8")),"final_model":model_description(final),
            "hardware_verified":False,"deployment_training":"all approved recordings after grouped validation",
            "limitations":["Only two same-person/device temporal collection rounds.",
                "Overlapping held-out windows remain correlated; no cross-person independence established.",
                "Feature subset is tested on the same CV groups used for previous candidates; selection is adaptive, not an untouched test.",
                "Offline results and header bytes do not measure on-board live accuracy, latency or memory."]}
        directory=destinations[method];directory.mkdir(parents=True,exist_ok=False)
        (directory/"metrics.json").write_text(json.dumps(metrics,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        (directory/"prm_model.h").write_text(header,encoding="utf-8")
        shutil.copyfile(manifest_path,directory/"manifest.json")
        with (directory/"heldout_predictions.csv").open("w",newline="",encoding="utf-8") as stream:
            writer=csv.writer(stream)
            writer.writerow(["recording_id","group_id","fold","true_state_id","predicted_state_id",*STATES])
            writer.writerows((r,g,int(f),int(t),int(pred),*map(float,p)) for r,g,f,t,pred,p in
                zip(recording_ids,groups,fold_ids,y,np.argmax(probabilities,axis=1),probabilities))
        np.savez_compressed(directory/"feature_windows.npz",features=original,masked_training_features=x,
            targets=y,recording_ids=recording_ids,group_ids=groups,folds=fold_ids,
            heldout_probabilities=probabilities,deployment_probabilities=final.predict_proba(original))
        results.append({"method_id":method,"version":"1","name":params["name"],
            "mean_fold_balanced_accuracy":metrics["mean_fold_balanced_accuracy"],
            "fold_balanced_accuracy_std":metrics["fold_balanced_accuracy_std"],**pooled,
            "header_bytes":metrics["export_header_bytes"],"result_directory":directory.as_posix()})
    summary={"comparison_id":"C02_invariant","version":"1","validation_strategy":strategy,
        "results":results,"hardware_verified":False,"selection_status":"not automatically selected/installed"}
    summary_root.mkdir(parents=True,exist_ok=False)
    (summary_root/"summary.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest",type=Path,nargs="?",default=Path("data/validated/manifest.json"))
    args=parser.parse_args()
    try:
        summary=compare(args.manifest)
    except (ValueError,OSError) as exc:
        parser.exit(2,f"Comparison failed: {exc}\n")
    for row in summary["results"]:
        print(f"{row['method_id']}: mean fold balanced={row['mean_fold_balanced_accuracy']:.6f}, "
              f"pooled accuracy={row['accuracy']:.6f}, macroF1={row['macro_f1']:.6f}, bytes={row['header_bytes']}")
