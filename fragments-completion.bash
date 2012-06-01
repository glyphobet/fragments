_UseFragments ()   # By convention, the function name
{                  # starts with an underscore.
  local curr prev cmd
  # Pointer to current completion word.
  # By convention, it's named "cur" but this isn't strictly necessary.

  COMPREPLY=()   # Array variable storing the possible completions.
  curr=${COMP_WORDS[COMP_CWORD]}
  prev=${COMP_WORDS[COMP_CWORD-1]}
  if [ $COMP_CWORD -gt "1" ] ; then
    cmd=${COMP_WORDS[1]}
  fi

  if [ "$cmd" == "apply" ] ; then
      case "$curr" in
        -*)
            COMPREPLY=( $( compgen -W '-i -a -U --unified' -- $curr ) );;
      esac;
  elif [ "$cmd" == "diff" -o "$cmd" == "fork" ] ; then
      case "$curr" in
        -*)
            COMPREPLY=( $( compgen -W '-U --unified' -- $curr ) );;
      esac;
  elif [ "$prev" == "fragments" -o "$cmd" == "help" ] ; then
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
        *)
            COMPREPLY=( $( compgen -W 'help init stat follow forget rename diff commit revert fork apply' -- $curr ) );;
      esac
  fi
  return 0
}

complete -F _UseFragments fragments
