from test.tel_send import send_message, send_photo


def tel_log(title: str, body: str, stk_cd: str | None = None):
    msg = f"[{title}]\n{body}"
    if stk_cd:
        msg = f"[{stk_cd}] {msg}"

    send_message(msg)
