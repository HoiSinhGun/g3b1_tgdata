from telegram import Update
from telegram.ext import CallbackContext

from model import CmdExe, G3Command


def cmd_pipe_exe(upd: Update, ctx: CallbackContext, cmd_li: list[G3Command]):
    if not ctx.args:
        ctx.args = []
    cmd_exe = CmdExe(cmd_li[0], ctx.args, cmd_li[1:])
    cmd_pipe_exe_recsv(upd, ctx, cmd_exe)


def cmd_pipe_exe_recsv(upd: Update, ctx: CallbackContext, cmd_exe: CmdExe):
    cmd_exe.res_cmd_li = []
    cmd_next = None if not cmd_exe.g3_cmd_li else cmd_exe.g3_cmd_li[0]
    cmd_after_next_li = [] if not cmd_exe.g3_cmd_li else cmd_exe.g3_cmd_li[1:]
    for line in cmd_exe.input:
        ctx.args.clear()
        split_li = line.split(' ')
        ctx.args.extend(split_li)
        res_str_li: list[str] = cmd_exe.g3_cmd.handler(upd, ctx)
        cmd_exe_next = CmdExe(cmd_next, res_str_li, cmd_after_next_li)
        cmd_exe.res_cmd_li.append(cmd_exe_next)
        if cmd_next:
            cmd_pipe_exe_recsv(upd, ctx, cmd_exe_next)


