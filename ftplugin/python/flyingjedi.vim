if get(b:, 'loaded_flyingjedi')
  finish
endif

setlocal completeopt+=noinsert

if !flyingjedi#is_running()
  call flyingjedi#start_server()
endif
call flyingjedi#set_root(get(g:, 'flyingjedi_root_filename', 'setup.py'))

inoremap <buffer> <C-x><C-o> <C-R>=flyingjedi#complete()<CR>
autocmd TextChangedI,InsertEnter <buffer> call flyingjedi#complete()
if get(g:, 'flyingjedi_override_completion')
  call flyingjedi#mapping()
endif

if !exists(':FlyingJediClear')
  command!  FlyingJediClear call flyingjedi#clear_cache()
endif

let b:loaded_flyingjedi = 1
