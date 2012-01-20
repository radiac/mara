"""
Prompt support
"""

@public
def prompt(user, prompt, callback, validate=None):
    """
    Send a prompt and get a single line in response
    The callback and validate functions will be passed:
        user    This user
        data    The response from the user
    The validate function must return a boolean value
    """
    user.write_raw(prompt)
    user.session('prompt').update({
        'prompt':   prompt,
        'callback': callback,
        'validate': validate
    })

@listen('input')
def input_prompt(e):
    data = e.user.session('prompt')
    if not data:
        return

    e.stop()

    if data['validate'] and not data['validate'](e.user, e.input):
        prompt(e.user, **data)
        return
    
    # Clear the prompt and get the callback
    callback = data['callback']
    data.clear()
    callback(e.user, e.input)
