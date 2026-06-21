from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown, worker_ready, setup_logging
from concurrent.futures import ThreadPoolExecutor

from app.configs.app_settings import settings
from app.workers.worker_settings import (
    SQS_VISIBILITY_TIMEOUT,
    SQS_POLLING_INTERVAL,
)
from app.dependencies.db import init_db_pool, close_db_pool
from app.dependencies.redis_client import init_redis_pool, close_redis_pool
from app.dependencies.storage import init_storage
from app.utils.logging import Logger, WorkerLog
from app.utils.seq_processor import SeqProcessor
from app.utils.llm_stubs import IS_E2E_MODE
from app.workers.tasks.plan import generate_plan as _generate_plan
from app.workers.tasks.code import generate_code as _generate_code
from app.workers.tasks.render import generate_render as _generate_render
from app.workers.tasks.seed import seed_knowledge as _seed_knowledge

app = Celery('mathanimate-worker',
             broker=settings.broker_url,
             backend=settings.redis_url)

if settings.environment == "prod":
    app.conf.update(
        broker_transport_options={
            'region': settings.aws_region,
            'visibility_timeout': SQS_VISIBILITY_TIMEOUT,
            'polling_interval': SQS_POLLING_INTERVAL,
            'predefined_queues': {
                'celery': {
                    'url': settings.sqs_queue_url,
                }
            }
        },
        task_default_queue='celery',
    )

logger = Logger.get_logger("worker")

if IS_E2E_MODE:
    logger.warning(WorkerLog(
        operation="e2e_mode",
        event="E2E mode enabled - LLM calls will be stubbed",
    ))

@setup_logging.connect
def _suppress_celery_logging(**kwargs):
    pass  # prevent Celery from overwriting structlog configuration


@worker_process_init.connect
def init_worker(**kwargs) -> None:
    SeqProcessor._executor = ThreadPoolExecutor(max_workers=1)
    init_storage()
    init_db_pool()
    init_redis_pool()


@worker_ready.connect
def on_worker_ready(**kwargs) -> None:
    init_db_pool()
    try:
        _seed_knowledge()
    except Exception:
        logger.warning(WorkerLog(
            operation="seed_knowledge",
            event="Knowledge auto-seed on startup failed; worker will continue",
        ), exc_info=True)
    finally:
        close_db_pool()


@worker_process_shutdown.connect
def shutdown_worker(**kwargs) -> None:
    close_db_pool()
    close_redis_pool()

generate_plan = app.task(name="generate_plan")(_generate_plan)
generate_code = app.task(name="generate_code")(_generate_code)
generate_render = app.task(name="generate_render")(_generate_render)
seed_knowledge = app.task(name="seed_knowledge")(_seed_knowledge)
