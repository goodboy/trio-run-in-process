import pickle
import signal
import os

import pytest
import trio

from trio_run_in_process import ProcessKilled, open_in_process


@pytest.mark.trio
async def test_open_in_proc_termination_while_running():
    async def do_sleep_forever():
        import trio

        await trio.sleep_forever()

    with trio.fail_after(2):
        async with open_in_process(do_sleep_forever) as proc:
            proc.terminate()
    assert proc.returncode == 15


@pytest.mark.trio
async def test_open_in_proc_cancel_via_fail_after():
    """Test that a ``trio`` initated timeout cancellation fails as expected.
    """
    async def do_sleep_forever():
        import trio

        await trio.sleep_forever()

    with pytest.raises(trio.TooSlowError):
        with trio.fail_after(0.5):
            async with open_in_process(do_sleep_forever):
                # should block forever here
                pass


@pytest.mark.trio
async def test_open_in_proc_kill_while_running():
    async def do_sleep_forever():
        import trio

        await trio.sleep_forever()

    with trio.fail_after(2):
        async with open_in_process(do_sleep_forever) as proc:
            proc.kill()
    assert proc.returncode == -9
    assert isinstance(proc.error, ProcessKilled)


@pytest.mark.trio
async def test_open_proc_interrupt_while_running():
    async def monitor_for_interrupt():
        import trio

        await trio.sleep_forever()

    with trio.fail_after(2):
        async with open_in_process(monitor_for_interrupt) as proc:
            proc.send_signal(signal.SIGINT)
        assert proc.returncode == 2


@pytest.mark.trio
async def test_open_proc_invalid_function_call():
    async def takes_no_args():
        pass

    with trio.fail_after(2):
        async with open_in_process(takes_no_args, 1, 2, 3) as proc:
            pass
        assert proc.returncode == 1
        assert isinstance(proc.error, TypeError)


@pytest.mark.trio
async def test_open_proc_unpickleable_params(touch_path):
    async def takes_open_file(f):
        pass

    with trio.fail_after(2):
        with pytest.raises(pickle.PickleError):
            with open(touch_path, "w") as touch_file:
                async with open_in_process(takes_open_file, touch_file):
                    # this code block shouldn't get executed
                    assert False


@pytest.mark.trio
async def test_open_proc_outer_KeyboardInterrupt():
    async def sleep_forever():
        import trio

        await trio.sleep_forever()

    with trio.fail_after(2):
        with pytest.raises(KeyboardInterrupt):
            async with open_in_process(sleep_forever) as proc:
                raise KeyboardInterrupt
        assert proc.returncode == 2


@pytest.mark.trio
async def test_open_in_proc_cancel_via_SIGINT():
    """Ensure that a control-C (SIGINT) signal cancels both the parent and
    child processes in trionic fashion
    """
    pid = os.getpid()

    async def do_sleep_forever():
        import trio

        await trio.sleep_forever()

    with trio.fail_after(2):
        async with open_in_process(do_sleep_forever):
            os.kill(pid, signal.SIGINT)
            await trio.sleep_forever()


@pytest.mark.trio
async def test_open_in_proc_cancel_via_SIGINT_other_task():
    """Ensure that a control-C (SIGINT) signal cancels both the parent
    and child processes in trionic fashion even a subprocess is started
    from a seperate ``trio`` child  task.
    """
    pid = os.getpid()

    async def do_sleep_forever():
        import trio

        await trio.sleep_forever()

    async def spawn_and_sleep_forever(task_status=trio.TASK_STATUS_IGNORED):
        async with open_in_process(do_sleep_forever):
            task_status.started()
            await trio.sleep_forever()

    with trio.fail_after(2):
        # should never timeout since SIGINT should cancel the current program
        async with trio.open_nursery() as n:
            await n.start(spawn_and_sleep_forever)
            os.kill(pid, signal.SIGINT)
