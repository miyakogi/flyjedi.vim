if get(b:, 'loaded_flyjedi')
  finish
endif

" version check
if !has('channel') || !has('job')
  echoerr '+channel and +job is required for flyjedi.vim'
  finish
endif

command! -buffer FlyJediEnable call flyjedi#enable()
command! -buffer FlyJediDisable call flyjedi#disable()
command! -buffer FlyJediClear call flyjedi#completion#clear_cache()
setlocal completeopt+=noinsert
setlocal omnifunc=flyjedi#dummyomni

if !get(g:, 'flyjedi_no_autostart')
  call flyjedi#enable()
endif
if !get(g:, 'flyjedi_no_keymap')
  let keybind = get(g:, 'flyjedi_complete_key', '<C-x><C-o>')
  execute 'inoremap <buffer> ' . keybind . ' <C-R>=flyjedi#completion#complete()<CR>'
endif

let b:loaded_flyjedi = 1
