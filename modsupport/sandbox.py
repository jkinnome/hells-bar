import lupa

lua = lupa.LuaRuntime(unpack_returned_tuples=True)

mod_api = lua.eval("""
{
    -- whitelist only specific string functions
    string = { format = string.format, len = string.len, sub = string.sub },

    -- game is restricted
    game   = nil,

    -- explicitly absent: os, io, require, package, debug, load, dofile,
    -- loadfile, rawget, rawset, getmetatable, setmetatable, ...
}
""")


def load_mod_script(script_text: str, game_api_table) -> None:
    chunk = lua.eval(f"load({script_text!r}, 'mod', 't', mod_api)")
    chunk()  # The mod literally cannot access anything outside mod_api
