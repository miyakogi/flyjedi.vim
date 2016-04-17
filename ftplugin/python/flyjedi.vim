if get(b:, 'loaded_flyjedi')
  finish
endif

" version check
if !has('channel') || !has('job')
  echoerr '+channel and +job is required for flyjedi.vim'
  finish
endif

setlocal completeopt+=noinsert

if !flyjedi#is_running()
  call flyjedi#start_server()
endif
call flyjedi#set_root(get(g:, 'flyjedi_root_filename', 'setup.py'))

inoremap <buffer> <C-x><C-o> <C-R>=flyjedi#complete()<CR>
autocmd TextChangedI,InsertEnter <buffer> call flyjedi#complete()
if get(g:, 'flyjedi_override_completion')
  call flyjedi#mapping()
endif

if !exists(':FlyJediClear')
  command!  FlyJediClear call flyjedi#clear_cache()
endif

let b:loaded_flyjedi = 1
