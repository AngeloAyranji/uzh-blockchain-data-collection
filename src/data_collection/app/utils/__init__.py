import logging
import time
from datetime import timedelta


def log_producer_progress(
    log: logging.Logger,
    i_block: int,
    start_block: int,
    end_block: int,
    progress_log_frequency: int,
    initial_time_counter: float,
    n_transactions: int,
):
    """Log a progress of the producer

    Shows current block number, total inserted blocks, total progress, estimated time until finish
    and total transactions in redis.
    """
    # Helper variables
    blocks_completed = i_block - start_block
    blocks_total = end_block - start_block
    # Check if this method should log now (every progress_log_frequency blocks)
    if (
        blocks_completed % progress_log_frequency == 0
        and blocks_completed > 0
        and blocks_total > 0
    ):
        blocks_left = blocks_total - blocks_completed
        # current block
        progress_str = f"Current block: #{i_block}"
        # progress
        progress = blocks_completed / blocks_total
        progress_str += f" | Progress {progress*100:.2f}% ({blocks_completed}/{blocks_total} blocks)"
        # average time
        avg_time_per_block = (
            time.perf_counter() - initial_time_counter
        ) / blocks_completed
        estimated_timedelta = timedelta(seconds=avg_time_per_block * blocks_left)
        td_str = str(estimated_timedelta).split(":")
        progress_str += f" | Estimated time to finish: {td_str[0]} h, {td_str[1]} min, {td_str[2]} s"
        # total transactions in redis / kafka topic
        progress_str += f" | total transactions in topic: {n_transactions}"
        log.info(progress_str)
