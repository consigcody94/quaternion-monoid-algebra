# Third-party data attribution

The stress tests in `tests/stress_tests.py` download public datasets at runtime to verify the algebra runs cleanly on real-world quaternion data. No dataset is bundled in this repository.

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

## EuRoC MAV Dataset (via the OpenVINS mirror)

- **Sequence:** Machine Hall 01 (`MH_01_easy`) ground truth, TUM trajectory format
- **Source:** the [OpenVINS](https://github.com/rpng/open_vins) repository's `ov_data/euroc_mav/MH_01_easy.txt`, pinned to commit `485d0dc4a421d9ff47aade93589a39c76a80a57d` (the original ETH ASL per-sequence downloads have moved to multi-gigabyte archives on the ETH Research Collection, DOI [10.3929/ethz-b-000690084](https://doi.org/10.3929/ethz-b-000690084))
- **License:** the ETH Research Collection archive of the dataset (DOI above) is marked **In Copyright – Non-Commercial Use Permitted** ([rightsstatements.org InC-NC 1.0](https://rightsstatements.org/page/InC-NC/1.0/), per the DataCite record). Treat the data as restricted to non-commercial use. This repository does not bundle the data; the stress test downloads it at runtime and uses the quaternion columns solely as a non-commercial correctness benchmark. OpenVINS itself is GPL-3.0 (the mirrored file is dataset content, not OpenVINS code)
- **SHA-256:** `ab1579de35a047d241e2d0d1a4f4306b4fa51d99c6f11bcdebf336ab2b784df9`

### Citation

If you use EuRoC MAV data in derived work, please cite:

> M. Burri, J. Nikolic, P. Gohl, T. Schneider, J. Rehder, S. Omari,
> M. W. Achtelik, R. Siegwart,
> "The EuRoC micro aerial vehicle datasets,"
> The International Journal of Robotics Research, 2016.

As with TUM, only the quaternion columns are used, as an independent public benchmark; neither the EuRoC authors nor the OpenVINS project are affiliated with this repository.
