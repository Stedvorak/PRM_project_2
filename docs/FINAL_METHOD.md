# Final Selected Method

Method ID: M02
Version: 1.0
Source file: scripts/train.py
Parameters: DecisionTreeClassifier(max_depth=4, min_samples_leaf=3, criterion='gini', random_state=42), window_samples=100 (2.0s), step_samples=25 (0.5s), 10 features: acc_mag_std, acc_mag_range, gyro_mag_std, gyro_mag_range, var_ax, var_ay, var_az, mean_ax, mean_az, log_var_acc_mag
Evaluation results: Train Accuracy = 99.78%, Test Accuracy = 100.00% (225 test windows from independent recording sessions, 0 classification errors)
Result files: firmware/include/model.h, firmware/include/bpm.h, outputs/evaluation.json
Local Git commit: 398d64b
Remote branch: antigravity
Verified remote commit: 398d64b
Verification status: VERIFIED
