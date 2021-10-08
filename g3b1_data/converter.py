import functools

from g3b1_cfg.tg_cfg import sel_ele_ty_cls


def ele_ty_converter():
    """Converts the return value if any and if conversion is supported"""

    def decorator_handler(cmd_func):
        @functools.wraps(cmd_func)
        def wrapper_handler(*args, **kwargs):
            output = cmd_func(*args, **kwargs)
            # checking for output instance eq EleVal => Not possible for some unknown reason: isinstance returns False
            # isinstance(output, EleVal)
            cls = sel_ele_ty_cls(output.ele_ty)
            if cls:
                output = cls.from_ele_val(output)

            return output

        return wrapper_handler

    return decorator_handler
