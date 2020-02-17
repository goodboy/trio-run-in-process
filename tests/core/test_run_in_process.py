import pytest
import trio

from trio_run_in_process import run_in_process


@pytest.mark.trio
async def test_run_in_process_touch_file(touch_path):
    async def touch_file(path: trio.Path):
        await path.touch()

    with trio.fail_after(2):
        assert not await touch_path.exists()
        await run_in_process(touch_file, touch_path)
        assert await touch_path.exists()


@pytest.mark.trio
async def test_run_in_process_with_result():
    async def return7():
        return 7

    with trio.fail_after(2):
        result = await run_in_process(return7)
    assert result == 7


@pytest.mark.trio
async def test_run_in_process_with_error():
    async def raise_err():
        raise ValueError("Some err")

    with trio.fail_after(2):
        with pytest.raises(ValueError, match="Some err"):
            await run_in_process(raise_err)


@pytest.mark.trio
async def test_run_in_process_timeout_via_cancel():

    async def sleep():
        import trio
        await trio.sleep_forever()

    with pytest.raises(trio.TooSlowError):
        with trio.fail_after(0.5):
            await run_in_process(sleep)


@pytest.mark.trio
async def test_run_in_process_timeout_via_cancel_inside_child():

    async def do_sleep():
        import trio
        with trio.fail_after(0.2):
            await trio.sleep(float('inf'))

    with pytest.raises(trio.TooSlowError):
        await run_in_process(do_sleep)
