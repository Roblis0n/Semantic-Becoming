function Code(el)
  -- xurl discards spaces inside nolinkurl. Preserve every source whitespace
  -- separately so mathematical factors/words cannot silently concatenate.
  local text=el.text:gsub('ᵀ','^T'); local result='{\\small'; local pos=1
  while pos<=#text do
    local first,last=text:find('%s+',pos)
    if not first then result=result..'\\nolinkurl{'..text:sub(pos)..'}'; break end
    if first>pos then result=result..'\\nolinkurl{'..text:sub(pos,first-1)..'}' end
    for _=first,last do result=result..'\\hspace{0.333em}' end
    pos=last+1
  end
  return pandoc.RawInline('latex',result..'}')
end
local function append_unicode(result,s)
  local pos=1
  while pos<=#s do
    local a=s:find('ᵀ',pos,true); local b=s:find('ć',pos,true)
    local i=(a and b) and math.min(a,b) or a or b
    if not i then result:insert(pandoc.Str(s:sub(pos)));break end
    if i>pos then result:insert(pandoc.Str(s:sub(pos,i-1))) end
    if i==a then result:insert(pandoc.RawInline('latex','\\textsuperscript{T}'));pos=i+#'ᵀ'
    else result:insert(pandoc.RawInline('latex','{\\fontspec{DejaVu Serif}ć}'));pos=i+#'ć' end
  end
end
function Str(el)
  local result=pandoc.List();local text=el.text;local pos=1
  while pos<=#text do
    local i,j=text:find('[A-Za-z0-9_%.%(%),=%-%^+]+',pos)
    if not i then append_unicode(result,text:sub(pos));break end
    if i>pos then append_unicode(result,text:sub(pos,i-1)) end
    local chunk=text:sub(i,j)
    if #chunk>12 or chunk:find('_') then result:insert(pandoc.RawInline('latex','\\nolinkurl{'..chunk..'}'))
    else result:insert(pandoc.Str(chunk)) end
    pos=j+1
  end
  return result
end
