"""
Prompt support
"""

def prompt(user, prompt, callback, validate=None):
    """
    Send a prompt and get a single line in response
    The callback and validate functions will be passed:
        user    This user
        data    The response from the user
    The validate function must return a boolean value
    """
    if not user.socket:
        return
    
    user.socket.send(prompt)
    user.store('prompt').update({
        'prompt':   prompt,
        'callback': callback,
        'validate': validate
    })

@listen('input')
def input_prompt(e):
    store = e.user.store('prompt')
    if not store:
        return

    e.stop()

    if store['validate'] and not store['validate'](e.user, e.input):
        prompt(e.user, **store)
        return
    
    # Clear the prompt and get the callback
    callback = store['callback']
    store.clear()
    callback(e.user, e.input)
