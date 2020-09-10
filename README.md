# QRS Comparison Web Server
## Setup
 - Install python3.7
 - Install most up-to-date version of wfdb (2.2.1). Ideally from github as the deployed version has some issues with
 reading and writing annotation/sample files.
 - Install all packages in requirements.txt
 - The host should have docker installed. Was programmed with docker-rootless.
 - Download if necessary datasets from physionet under /mnt/dsets/physionet
 (aami-ec13  afdb  edb  mitdb  nsrdb  nstdb  svdb  vfdb)
 - start app with the following commands
```export FLASK_APP=src/application.py
export FLASK_ENV=development
export FLASK_DEBUG=0
echo $FLASK_APP
echo $FLASK_ENV
echo $FLASK_DEBUG
python3.7 -u -m flask run --host=0.0.0.0 -p 5001
```

## Submitting Algorithms
You can find examples under test/algorithms. Each folder in this directory can be zipped and uploaded. Every .zip file needs to contains a shell script called "setup.sh" which will then be executed. In this script you need to deploy and execute your algorithm on the data saved under /data/. Please save your predictions in the format of physionet https://physionet.org/about/database/) under the /pred/ path.
