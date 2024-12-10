import os
import base64
from httpx import HTTPStatusError
import traceback
import time

from src.job import Job
from src.logging import logger

def start_create_resume(resume_generator_manager, job):
    folder_path = 'generated_cv'
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    job_title = job.get('title')
    company_name = job.get('company')
    job_description = job.get('description')
    print(job_title, company_name, job_description)
    job = Job(
        title=job_title,
        company=company_name,
        description=job_description
    )
    while True:
        try:
            timestamp = int(time.time())
            file_path_pdf = os.path.join(folder_path, f"CV_{job.company}_{timestamp}.pdf")
            logger.debug(f"Generated file path for resume: {file_path_pdf}")

            logger.debug(f"Generating resume for job: {job.title} at {job.company}")
            resume_pdf_base64 = resume_generator_manager.pdf_base64(job_description_text=job.description)
            with open(file_path_pdf, "xb") as f:
                f.write(base64.b64decode(resume_pdf_base64))
            logger.debug(f"Resume successfully generated and saved to: {file_path_pdf}")

            break
        except HTTPStatusError as e:
            if e.response.status_code == 429:

                retry_after = e.response.headers.get('retry-after')
                retry_after_ms = e.response.headers.get('retry-after-ms')

                if retry_after:
                    wait_time = int(retry_after)
                    logger.warning(f"Rate limit exceeded, waiting {wait_time} seconds before retrying...")
                elif retry_after_ms:
                    wait_time = int(retry_after_ms) / 1000.0
                    logger.warning(f"Rate limit exceeded, waiting {wait_time} milliseconds before retrying...")
                else:
                    wait_time = 20
                    logger.warning(f"Rate limit exceeded, waiting {wait_time} seconds before retrying...")

                time.sleep(wait_time)
            else:
                logger.error(f"HTTP error: {e}")
                raise

        except Exception as e:
            logger.error(f"Failed to generate resume: {e}")
            tb_str = traceback.format_exc()
            logger.error(f"Traceback: {tb_str}")
            if "RateLimitError" in str(e):
                logger.warning("Rate limit error encountered, retrying...")
                time.sleep(20)
            else:
                raise