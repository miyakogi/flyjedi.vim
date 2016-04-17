# flyingjedi.vim

Successor of [miyakogi/asyncjedi](https://github.com/miyakogi/asyncjedi).

## Features

- Asynchronous, non-blocking auto-completion
- Fast startup
- Fuzzy completion
- Virtualenv support

Lots of other jedi's features (goto, rename, usage, and so on) are not implemented.
If you need these features, please use [jedi-vim](https://github.com/davidhalter/jedi-vim) plugin.
This plugin will not conflict with jedi-vim if you disable the auto completion of jedi-vim.

## Requirements

- Vim with `+job` and `+channel` features
- Python 3.4+
- Jedi
    - If you use virtualenv, need jedi installed in the virtualenv

## Usage

This plugin will conflict with other completion plugins.
So you need to disable it.

Example (neocomplete)

```vim
" write after the above setting
autocmd myvimrc FileType python NeoCompleteLock
```

If you use with jedi-vim plugin, please disable its completions.

```vim
let g:jedi#completions_enabled = 0
```

## Configuration

### Project root

This plugin searches `setup.py` upwards from the current file, to find the project root.
If you want to use another file name, for example `.gitignore`, add the following setting.

```vim
let g:flyingjedi_root_filename = '.gitignore'
```

### Additional information

By default, this plugin does not show additional information about completion items.

If you prefer to show additional information, please add the bellow setting.

```vim
let g:flyingjedi_detail_info = 1
" or, for buffer
" let b:flyingjedi_detail_info = 1
```

#### Caution

Jedi sometimes takes too long time to get additional information, docstring/descriptions.
If you encounter a performance issue, please disable this option.
