let s:pyserver = expand('<sfile>:p:h:h') . '/flyjedi'
let s:handlers = []
let s:port = -1

function! flyjedi#set_root() abort
  let fname = get(g:, 'flyjedi_root_filename', 'setup.py')
  let file = findfile(fname, escape(expand('<afile>:p:h'), ' ') . ';')
  if l:file != ''
    let b:flyjedi_root_dir = substitute(l:file, '/' . fname . '$', '', 'g' )
  endif
endfunction

function! flyjedi#is_running() abort
  if s:port > 0
    return v:true
  else
    return v:false
  endif
endfunction

function! flyjedi#dummyomni(findstart, base) abort
  return a:findstart ? -3 : []
endfunction

function! flyjedi#server_cd(ch, msg) abort
  if a:msg =~ '\m^\d\+$'
    let s:port = str2nr(a:msg)
  elseif a:msg == '' || a:msg ==# 'DETACH'
    return
  else
    echomsg 'FlyJediServer: ' . string(a:msg)
  endif
endfunction

function! flyjedi#setup_channel() abort
  let ch = ch_open('localhost:' . s:port, {'mode': 'json', 'waittime': 3})
  let st = ch_status(ch)
  if st !=# 'open'
    echoerr 'channel error: ' . st
  endif
  return ch
endfunction

function! s:clear_channel() abort
  for ch in s:handlers
    if ch_status(ch) ==# 'open'
      call ch_close(ch)
    endif
  endfor
endfunction

function! flyjedi#close_channel(ch) abort
  call ch_close(a:ch)
  let ind = index(s:handlers, a:ch)
  if ind >= 0
    call remove(s:handlers, ind)
  endif
endfunction

function! flyjedi#send(ch, msg, ...) abort
  if a:0 > 0
    let cb = a:1
  else
    let cb = {}
  endif
  call ch_sendexpr(a:ch, a:msg, cb)
  call s:clear_channel()
  let s:handlers = [a:ch]
endfunction

function! flyjedi#start_server() abort
  call flyjedi#set_root()
  let ch = ch_open('localhost:8891', {'waittime': 10})
  if ch_status(ch) ==# 'open'
    " for debug
    let s:port = 8891
    echomsg 'FlyJedi: use debug server at localhost:8891'
    call ch_close(ch)
  else
    let cmd = ['python3', s:pyserver]
    let s:server = job_start(cmd, {'callback': 'flyjedi#server_cd'})
  endif
endfunction

function! flyjedi#enable() abort
  if !flyjedi#is_running()
    call flyjedi#start_server()
  endif
  augroup flyjedi
    autocmd TextChangedI,InsertEnter <buffer> call flyjedi#completion#complete()
  augroup END
endfunction

function! flyjedi#disbable() abort
  augroup flyjedi
    autocmd!
  augroup END
endfunction
