if get(b:, 'loaded_flyjedi')
  finish
endif

" version check
if !has('channel') || !has('job')
  echoerr '+channel and +job is required for flyjedi.vim'
  finish
endif

setlocal completeopt+=noinsert
setlocal omnifunc=flyjedi#dummyomni
inoremap <buffer> <C-x><C-o> <C-R>=flyjedi#complete()<CR>
autocmd TextChangedI,InsertEnter <buffer> call flyjedi#complete()

if !flyjedi#is_running()
  call flyjedi#start_server()
endif

if !exists(':FlyJediClear')
  command!  FlyJediClear call flyjedi#clear_cache()
endif

let b:loaded_flyjedi = 1
