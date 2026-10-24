-- Pandoc filter for kit documentation.
-- ::: complete ... :::  marks text the bank completes:
--   Word  -> paragraph style "To complete" (shaded orange)
--   LaTeX -> shaded box with a "To complete" label
function Div(el)
  if not el.classes:includes("complete") then return nil end
  if FORMAT:match("docx") then
    el.attributes["custom-style"] = "To complete"
    return el
  elseif FORMAT:match("latex") then
    local out = { pandoc.RawBlock("latex", "\\begin{tocomplete}") }
    for _, b in ipairs(el.content) do table.insert(out, b) end
    table.insert(out, pandoc.RawBlock("latex", "\\end{tocomplete}"))
    return out
  end
end
