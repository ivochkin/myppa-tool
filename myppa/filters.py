#!/usr/bin/env python3

def format_deb_depends(depends):
    dependlist = []
    for pkgname, verspec in depends.items():
        dependstr = pkgname
        if verspec is None:
            dependlist.append(pkgname)
            continue
        if isinstance(verspec, str):
            dependlist.append("{} (= {})".format(pkgname, verspec))
            continue
        version_cmp_to_symbol = {
            "version": "=",
            "version-greater": ">>",
            "version-later": ">>",
            "version-less": "<<",
            "version-earlier": "<<",
            "version-greater-or-equal": ">=",
            "version-later-or-equal": ">=",
            "version-less-or-equal": "<=",
            "version-earlier-or-equal": "<=",
            "version-not-greater": "<=",
            "version-not-later": "<=",
            "version-not-less": ">=",
            "version-not-earlier": ">=",
        }
        for vercmp, symbol in version_cmp_to_symbol.items():
            if vercmp in verspec:
                dependstr += " ({} {})".format(symbol, verspec[vercmp])
                break
        if "platform" in verspec:
            dependstr += " [{}]".format(verspec["platform"])
        elif "excluding-platform" in verspec:
            dependstr += " [!{}]".format(verspec["excluding-platform"])
        dependlist.append(dependstr)
    return ", ".join(dependlist)
