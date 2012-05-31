# file: UseGetOpt-2
# UseGetOpt-2.sh parameter-completion

_UseFragments ()   # By convention, the function name
{                  # starts with an underscore.
  local cur prev
  # Pointer to current completion word.
  # By convention, it's named "cur" but this isn't strictly necessary.

  COMPREPLY=()   # Array variable storing the possible completions.
  curr=${COMP_WORDS[COMP_CWORD]}
  prev=${COMP_WORDS[COMP_CWORD-1]}

  if [ "$prev" == "apply" ] ; then
      case "$curr" in
        -*)
            COMPREPLY=( $( compgen -W '-i -a -U --unified' -- $curr ) );;
      esac;
  elif [ "$prev" == "diff" -o "$prev" == "fork" ] ; then
      case "$curr" in
        -*)
            COMPREPLY=( $( compgen -W '-U --unified' -- $curr ) );;
      esac;
  elif [ "$prev" == "fragments" -o "$prev" == "help" ] ; then
      case "$curr" in
        a*)
            COMPREPLY=( $( compgen -W 'apply' -- $curr ) );;
        c*)
            COMPREPLY=( $( compgen -W 'commit' -- $curr ) );;
        d*)
            COMPREPLY=( $( compgen -W 'diff' -- $curr ) );;
        h*)
            COMPREPLY=( $( compgen -W 'help' -- $curr ) );;
        i*)
            COMPREPLY=( $( compgen -W 'init' -- $curr ) );;
        f*)
            COMPREPLY=( $( compgen -W 'follow forget fork' -- $curr ) );;
        r*)
            COMPREPLY=( $( compgen -W 'rename revert' -- $curr ) );;
        s*)
            COMPREPLY=( $( compgen -W 'stat' -- $curr ) );;
        '')
            COMPREPLY=( $( compgen -W 'help init stat follow forget rename diff commit revert fork apply' -- $curr ) );;
      esac
  fi
  return 0
}

complete -F _UseFragments fragments
