# Third-party data attribution

The stress test `tests/stress_tests.py` downloads a public dataset from TU Munich at runtime to verify the algebra runs cleanly on real-world quaternion data. The dataset is not bundled in this repository.

## TUM RGB-D Dataset

- **Sequence:** `rgbd_dataset_freiburg2_pioneer_360-groundtruth.txt`
- **Source:** [https://cvg.cit.tum.de/rgbd/dataset/freiburg2/](https://cvg.cit.tum.de/rgbd/dataset/freiburg2/)
- **License:** Creative Commons Attribution 4.0 (CC BY 4.0)
- **SHA-256:** `1338bae01eb0219fcfc59b0c1a28c2ee091e36a6490f0cc022846328cebc1a60`

### Citation

If you use TUM RGB-D data in derived work, please cite:

> J. Sturm, N. Engelhard, F. Endres, W. Burgard, D. Cremers,
> "A Benchmark for the Evaluation of RGB-D SLAM Systems,"
> Proc. of the International Conference on Intelligent Robot Systems (IROS), 2012.

The stress test in this repository uses only the ground-truth quaternion columns as test input to demonstrate that the algebra handles real-world motion-captured rotation data without numerical failure. The TUM authors are not affiliated with this project; their data is used as an independent public benchmark.
