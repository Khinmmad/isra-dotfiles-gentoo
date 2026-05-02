typeset -g POWERLEVEL9K_INSTANT_PROMPT=off

# Enable Powerlevel10k instant prompt
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"

plugins=(sudo git zsh-autosuggestions)

source $ZSH/oh-my-zsh.sh

# Aliases (lsd fallback)
if command -v lsd &>/dev/null; then
    alias ls='lsd'
    alias ll='lsd -la'
    alias lt='lsd --tree'
else
    alias ls='ls --color=auto'
    alias ll='ls -la --color=auto'
    alias lt='tree -a -C --dirsfirst'
fi

# Gentoo aliases
alias emerge-search='emerge -s'
alias emerge-info='emerge --info'
alias update-world='sudo emerge -avuDN @world'
alias clean-packages='sudo eclean-dist --deep && sudo eclean-pkg --deep'
alias revdep='sudo revdep-rebuild'
alias sync-portage='sudo emerge --sync'

# Zsh plugins (Gentoo paths)
[[ -f /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]] && \
  source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
[[ -f /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ]] && \
  source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh

# Fastfetch on login
(( ${+commands[fastfetch]} )) && fastfetch

# Yazi - terminal file manager with cwd sync
function y() {
    local tmp="$(mktemp -t "yazi-cwd.XXXXXX")"
    yazi "$@" --cwd-file="$tmp"
    if cwd="$(cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
        cd -- "$cwd"
    fi
    rm -f -- "$tmp"
}

# npm global bin in PATH
export PATH="$PATH:$(npm prefix -g)/bin"

# Zoxide (if installed)
(( ${+commands[zoxide]} )) && eval "$(zoxide init zsh)"

# Fzf (if installed)
[[ -f ~/.fzf.zsh ]] && source ~/.fzf.zsh

# Powerlevel10k config
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
