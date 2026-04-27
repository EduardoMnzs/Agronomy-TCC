import sys
from celery.bin.celery import main

sys.argv = ["celery", "-A", "workers.celery_app", "flower",
            "--port=5555", "--address=0.0.0.0"]
sys.exit(main())
