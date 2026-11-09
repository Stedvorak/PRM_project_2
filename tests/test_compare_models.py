"""Synthetic software-only fixtures; never real model evaluation evidence."""
import json
from pathlib import Path
import subprocess

import numpy as np
import pytest

from tools.compare_models import (CANDIDATES, compare, estimator_for, export_model,
                                  group_folds, grouped_dataset)
from tools.train_model import COLUMNS, STATES


def make_manifest(tmp_path):
    recordings=[]
    for round_id in range(2):
        for state_id,state in enumerate(STATES):
            path=tmp_path/f"{state}_round{round_id}.csv"
            data=np.zeros((150,7))
            data[:,0]=np.arange(150)*40
            data[:,1]=state_id*0.3+round_id*0.001
            data[:,3]=1
            data[:,4]=np.sin(np.arange(150)*0.1)*(state_id+1)
            np.savetxt(path,data,delimiter=",",header=",".join(COLUMNS),comments="")
            recordings.append({"recording_id":path.stem,"path":path.name,"state":state,
                               "group_id":f"round{round_id}"})
    path=tmp_path/"test_only_manifest.json"
    path.write_text(json.dumps({"source":"real_sensor","sample_rate_hz":25,
                                "recordings":recordings}),encoding="utf-8")
    return path


def test_grouped_rounds_keep_all_windows_of_every_recording_together(tmp_path):
    _,x,y,ids,groups=grouped_dataset(make_manifest(tmp_path))
    strategy,folds=group_folds(y,groups)
    assert strategy=="leave_one_whole_collection_group_out"
    assert len(folds)==2
    for fold in folds:
        train,test=fold["train"],fold["test"]
        assert not set(groups[train]) & set(groups[test])
        assert not set(ids[train]) & set(ids[test])
        assert set(y[train])==set(y[test])==set(range(4))


def test_class_specific_bouts_are_stratified_without_group_leakage():
    y=np.repeat(np.arange(4),6)
    groups=np.array([f"class{c}_bout{b}" for c in range(4) for b in range(2) for _ in range(3)])
    _,folds=group_folds(y,groups)
    assert len(folds)==2
    for fold in folds:
        assert not set(groups[fold["train"]]) & set(groups[fold["test"]])
        assert set(y[fold["test"]])==set(range(4))


def test_insufficient_groups_and_missing_group_declaration_rejected(tmp_path):
    y=np.repeat(np.arange(4),3)
    with pytest.raises(ValueError,match="two"):
        group_folds(y,np.array(["only_round"]*12))
    path=make_manifest(tmp_path)
    raw=json.loads(path.read_text())
    del raw["recordings"][0]["group_id"]
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError,match="group_id"):
        grouped_dataset(path)


def test_comparison_exports_candidates_and_refuses_overwrite(tmp_path):
    manifest=make_manifest(tmp_path)
    output=tmp_path/"synthetic_test_results"
    summary_dir=tmp_path/"synthetic_test_comparison"
    summary=compare(manifest,output,"test",summary_dir)
    assert len(summary["results"])==4
    for method in CANDIDATES:
        directory=output/f"{method}_vtest"
        metrics=json.loads((directory/"metrics.json").read_text())
        assert metrics["hardware_verified"] is False
        assert len(metrics["folds"])==2
        assert (directory/"prm_model.h").exists()
        data=np.load(directory/"feature_windows.npz")
        assert np.isfinite(data["heldout_probabilities"]).all()
        assert np.isfinite(data["deployment_probabilities"]).all()
    with pytest.raises(FileExistsError):
        compare(manifest,output,"test",summary_dir)


def test_folded_logistic_parameters_match_sklearn_probabilities():
    rng=np.random.default_rng(42)
    x=rng.normal(size=(100,12)).astype(np.float32)*np.arange(1,13)
    y=np.arange(100)%4
    estimator=estimator_for("M04").fit(x,y)
    scaler=estimator.named_steps["standardscaler"]
    model=estimator.named_steps["logisticregression"]
    weight=model.coef_/scaler.scale_[None,:]
    bias=model.intercept_-weight@scaler.mean_
    logits=x@weight.T+bias
    p=np.exp(logits-logits.max(axis=1,keepdims=True))
    p/=p.sum(axis=1,keepdims=True)
    np.testing.assert_allclose(p,estimator.predict_proba(x),atol=1e-7,rtol=1e-6)


@pytest.mark.parametrize("method",list(CANDIDATES))
def test_each_generated_header_compiles_for_esp32(tmp_path,method):
    root=Path(__file__).resolve().parents[1]
    compiler=root/".pio-core/packages/toolchain-xtensa-esp32s3/bin/xtensa-esp32s3-elf-g++.exe"
    if not compiler.exists():
        pytest.skip("ESP32 target compiler not installed")
    rng=np.random.default_rng(43)
    x=rng.normal(size=(80,12)).astype(np.float32)
    y=np.arange(80)%4
    estimator=estimator_for(method).fit(x,y)
    header=tmp_path/"candidate.h"
    header.write_text(export_model(estimator,method,"test"),encoding="utf-8")
    source=tmp_path/"probe.cpp"
    source.write_text('#include "candidate.h"\nint main(){float x[12]={};float p[4];return prm::predictProbabilities(x,p)?0:1;}\n',encoding="utf-8")
    result=subprocess.run([str(compiler),"-std=gnu++11","-Wall","-Werror","-fsyntax-only",
                           "-I",str(root/"firmware/include"),str(source)],
                          capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
