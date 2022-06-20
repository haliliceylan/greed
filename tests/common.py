import IPython
import argparse
import logging

from SEtaac import Project, utils
from SEtaac.utils import gen_exec_id


def setup_logging():
    LOGGING_FORMAT = "%(levelname)s | %(name)s | %(message)s"
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--target", type=str, action="store", help="Path to Gigahorse output folder")

    args = parser.parse_args()

    # setup logging
    if args.debug:
        logging.getLogger("SEtaac").setLevel("DEBUG")
    else:
        logging.getLogger("SEtaac").setLevel("INFO")

    return args


def parse_log(state):
    log_stmt = state.curr_stmt

    # manually set arg_vals, since we didn't handle this statement yet
    log_stmt.set_arg_val(state)

    if not (log_stmt.offset_val == 0 and log_stmt.size_val == 0):
        return

    # length_ptr = log_stmt.topic_val
    # length = utils.bytes_to_int(state.memory.read(length_ptr, 32))
    #
    # value_ptr = log_stmt.topic_val + 32
    # value = bytes(state.memory.read(value_ptr, length)).decode()

    value = utils.int_to_big_endian(log_stmt.topic_val).decode().split('\x00')[0]

    print(f"---> {value}")
    outcome, testname = value.split(":")
    assert outcome == "success", f"{testname} failed"


def run_test(target_dir, debug=False):
    p = Project(target_dir=target_dir)

    xid = gen_exec_id()
    entry_state = p.factory.entry_state(xid=xid)
    simgr = p.factory.simgr(entry_state=entry_state)

    while len(simgr.active) > 0:
        simgr.run(find=lambda s: s.curr_stmt.__internal_name__ == "LOG1")
        for s in simgr.found:
            parse_log(s)

        simgr.move(from_stash="found", to_stash="active")

    if debug:
        IPython.embed()
