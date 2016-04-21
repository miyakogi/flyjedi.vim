if get(b:, 'loaded_flyjedi')
  finish
endif

" version check
if !has('channel') || !has('job')
  echoerr '+channel and +job is required for flyjedi.vim'
  finish
endif

call flyjedi#initialize_buffer()

let b:loaded_flyjedi = 1
