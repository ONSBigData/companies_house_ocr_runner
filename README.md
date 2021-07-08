# companies_house_ocr_runner

Runs Tesseract OCR over PDF paper filings from Companies House.

This project is tightly coupled to a specific deployment scenario.
It also makes assumptions about what data is available in the environment.

For running in another environment it would probably be simplest to review how this works
and then create a similar application.

To learn how to call Tesseract from the command line in an efficient way see:
the `run_ocr` function in [tesseract_wrapper](src/ch_ocr_runner/images/tesseract_wrapper.py). 

NOTE: This project was created as a prototype

### Running locally

To run locally with Vagrant/VirtualBox:

* Install Vagrant/VirtualBox
* Then:

```shell script
  vagrant up
  vagrant ssh
  vagrant@ubuntu-bionic:~$ ch_ocr_runner
```

To run locally or on any web server with Docker:

* Install Docker and Docker Compose
* Create a resources directory in the project root (Gets mounted at `/var/resources` in the container)
* Copy `ch_ocr_runner_config.docker-example.yml` to `ch_ocr_runner_config.yml`
* Then:

```shell script
  docker-compose up
```

### Environment variables

Batch allocation is done with an environment variable:

    CH_OCR_MACHINE_ID="UNIQUE_NAME"

To maximise CPU usage for batch processing we start multiple Tesseract processes,
but restrict each one to use a single processor by setting:

    OMP_THREAD_LIMIT = 1
    
### Stop/start running

Each batch gets a directory in the working area.
When a batch is finished a batch lock file is created.
As long as that file is present future runs won't repeat that batch.


