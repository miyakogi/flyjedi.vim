let s:python_string_syntax = ['pythonString', 'pythonComment', 'pythonQuotes', 'pythonTripleQuotes']

function! s:init_msg() abort
  let msg = {}
  let msg.line = line('.')
  let msg.col = col('.')
  let msg.path = expand('%:p')
  let msg.root = get(b:, 'flyjedi_root_dir')
  return msg
endfunction

function! flyjedi#completion#cb(ch, msg) abort
  if mode() ==# 'i' && expand('%:p') ==# a:msg.path
    if a:msg.success
      call complete(a:msg.start_col, a:msg.items)
    elseif a:msg.mode ==# 'path'
      call feedkeys("\<C-x>\<C-f>")
    elseif a:msg.mode ==# 'string'
      call feedkeys("\<C-x>\<C-n>")
    endif
  endif
  call flyjedi#close_channel(a:ch)
endfunction

function! s:is_string() abort
  return index(s:python_string_syntax, synIDattr(synID(line('.'), col('.'), 0), 'name')) >= 0
endfunction

function! s:complete_string() abort
  let msg = s:init_msg()
  let msg['action'] = 'completion'
  let msg['mode'] = 'string'
  let msg.text = getline('.')
  return msg
endfunction

function! s:complete_python() abort
  let msg = s:init_msg()
  let msg['action'] = 'completion'
  let msg['mode'] = 'python'
  let msg.text = getline(0, '$')
  let msg.detail = get(b:, 'flyjedi_detail_info', get(g:, 'flyjedi_detail_info'))
  let msg.fuzzy = !get(b:, 'flyjedi_no_fuzzy', get(g:, 'flyjedi_no_fuzzy'))
  let msg.icase = !get(b:, 'flyjedi_no_icase', get(g:, 'flyjedi_no_icase'))
  return msg
endfunction

function! s:complete() abort
  if flyjedi#is_running()
    let ch = flyjedi#setup_channel()
    if s:is_string()
      let msg = s:complete_string()
    else
      let msg = s:complete_python()
    endif
    call flyjedi#send(ch, msg, {'callback': 'flyjedi#completion#cb'})
  else
    echomsg 'server not running'
  endif
endfunction

function! flyjedi#completion#complete() abort
  call s:complete()
  return ''
endfunction

function! flyjedi#completion#clear_cache() abort
  if flyjedi#is_running()
    let ch = ch_open('localhost:' . flyjedi#port, {'mode': 'json'})
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
