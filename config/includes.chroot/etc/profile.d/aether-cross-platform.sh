# AETHER OS Cross-Platform Shell Environment
# Provides seamless aliases and ergonomics for Windows, macOS, and Linux users

# Windows aliases
alias cls='clear'
alias dir='ls -la --group-directories-first --color=auto'
alias copy='cp -iv'
alias move='mv -iv'
alias del='rm -iv'
alias erase='rm -iv'
alias md='mkdir -p'
alias rd='rmdir'
alias ren='mv -iv'
alias type='cat'
alias findstr='grep -rnI'
alias fc='diff -u'
alias comp='diff -u'
alias attrib='ls -ld'
alias tracert='traceroute'
alias where='which -a'
alias ver='echo "AETHER OS [Version 2.5.0 - Debian 13 Trixie based]"'

# Linux enhancements
alias ll='ls -alF --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'
alias grep='grep --color=auto'
alias egrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'
alias df='df -h'
alias free='free -m'

# Ensure batcat is called when bat is used if available
if command -v batcat >/dev/null 2>&1 && ! command -v bat >/dev/null 2>&1; then
    alias bat='batcat'
fi
