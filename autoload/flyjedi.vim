let s:pyserver = expand('<sfile>:p:h:h') . '/flyjedi'
let s:handlers = []

function! flyjedi#set_root() abort
  let fname = get(g:, 'flyjedi_root_filename', 'setup.py')
  let file = findfile(fname, escape(expand('<afile>:p:h'), ' ') . ';')
  if l:file != ''
    let b:flyjedi_root_dir = substitute(l:file, '/' . fname . '$', '', 'g' )
  endif
endfunction

function! flyjedi#is_running() abort
  if exists('s:port')
    return v:true
  else
    return v:false
  endif
endfunction

function! s:setup_channel() abort
  let ch = ch_open('localhost:' . s:port, {'mode': 'json', 'waittime': 3})
  let st = ch_status(ch)
  if st !=# 'open'
    echoerr 'channel error: ' . st
  endif
  return ch
endfunction

function! s:init_msg() abort
  let msg = {}
  let msg.line = line('.')
  let msg.col = col('.')
  let msg.text = getline(0, '$')
  let msg.path = expand('%:p')
  let msg.root = get(b:, 'flyjedi_root_dir')
  return msg
endfunction

function! s:send(ch, msg, ...) abort
  if a:0 > 0
    let cb = a:1
  else
    let cb = {}
  endif
  call ch_sendexpr(a:ch, a:msg, cb)
  call s:ch_clear()
  let s:handlers = [a:ch]
endfunction

function! flyjedi#dummyomni(findstart, base) abort
  return a:findstart ? -3 : []
endfunction

function! flyjedi#complete_cb(ch, msg) abort
  call ch_close(a:ch)
  if mode() ==# 'i' && expand('%:p') ==# a:msg.path
    if a:msg.mode ==# 'grammer'
      call complete(a:msg.start_col, a:msg.items)
    elseif a:msg.mode ==# 'path'
      call feedkeys("\<C-x>\<C-f>")
    elseif a:msg.mode ==# 'string'
      call feedkeys("\<C-x>\<C-n>")
    endif
  endif
  let ind = index(s:handlers, a:ch)
  if ind >= 0
    call remove(s:handlers, ind)
  endif
endfunction

function! s:complete() abort
  if flyjedi#is_running()
    let ch = s:setup_channel()
    let msg = s:init_msg()
    let msg['mode'] = 'completion'
    let msg.detail = get(b:, 'flyjedi_detail_info', get(g:, 'flyjedi_detail_info'))
    let msg.fuzzy = !get(b:, 'flyjedi_no_fuzzy', get(g:, 'flyjedi_no_fuzzy'))
    let msg.icase = !get(b:, 'flyjedi_no_icase', get(g:, 'flyjedi_no_icase'))
    call s:send(ch, msg, {'callback': 'flyjedi#complete_cb'})
  endif
  return ''
endfunction

function! flyjedi#complete() abort
  call s:complete()
  return ''
endfunction

function! flyjedi#clear_cache() abort
  if flyjedi#is_running()
    let ch = ch_open('localhost:' . s:port, {'mode': 'json'})
    let st = ch_status(ch)
    if st ==# 'open'
      let msg = {'clear_cache':1}
      call ch_sendexpr(ch, msg)
    else
      echomsg 'channel error: ' . st
    endif
  endif
  return ''
endfunction

function! s:ch_clear() abort
  for ch in s:handlers
    if ch_status(ch) ==# 'open'
      call ch_close(ch)
    endif
  endfor
endfunction

function! flyjedi#server_started(ch, msg) abort
  if a:msg =~ '\m^\d\+$'
    let s:port = str2nr(a:msg)
  elseif a:msg == '' || a:msg ==# 'DETACH'
    return
  else
    echomsg 'FlyJediServer message: ' . string(a:msg)
  endif
endfunction

function! flyjedi#wrap_ce(s) abort
  return "\<C-e>" . a:s
endfunction

let s:closepum=' <C-r>=pumvisible()?flyjedi#wrap_ce("'
function! s:map(s) abort
  let cmd = 'inoremap <buffer><silent> ' . a:s . s:closepum . a:s . '"):"' . a:s . '"<CR>'
  execute cmd
endfunction

function! flyjedi#mapping() abort
  for k in split('abcdefghijklmnopqrstuvwxyz', '\zs')
    call s:map(k)
    call s:map(toupper(k))
  endfor
  for k in split('123456789', '\zs')
    call s:map(k)
  endfor
  call s:map('_')
  call s:map('@')
  call s:map('\<BS>')
  call s:map('\<C-h>')
endfunction

function! flyjedi#start_server() abort
  call flyjedi#set_root()
  let ch = ch_open('localhost:8891', {'waittime': 10})
  if ch_status(ch) ==# 'open'
    " for debug
    let s:port = 8891
    echomsg 'flyjedi: use debug server at localhost:8891'
    call ch_close(ch)
  else
    let cmd = ['python3', s:pyserver]
    let s:server = job_start(cmd, {'callback': 'flyjedi#server_started'})
  endif
endfunction
