"""
Admin commands
"""

@command
def reload(e):
    manager.reload()
    write_all('-- Reloading plugins --')
