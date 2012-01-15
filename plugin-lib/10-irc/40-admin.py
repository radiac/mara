"""
Admin commands
"""

@command('reload')
def cmd_reload(e):
    manager.reload()
    write_all('-- Reloading plugins --')
