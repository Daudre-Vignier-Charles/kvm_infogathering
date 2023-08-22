#!/bin/bash

p_help(){
    cat <<-EOF
Usage: start.sh [OPTION]...
Start gathering information from listed servers.
-h  --help          :   display this help
-o  --offline       :   perform only the generation of the html files from downloaded data
                        in offline mode no connection to a server will be made
-c  --to-csv        :   export data as CSV instead of HTML files

Configuration is first loaded from config.sh but this can be overridden with one of these following options:
-r  --report-directory PATH
            Raw data and html files location
-s  --servers SERVER1[,SERVER2]...
            Comma separated list of KVM servers
-i  --ssh-cert CERT
            Path of the certificate used to connect to the KVM servers
-u  --ssh-user USER
            Remote user used to connect to the KVM servers
EOF
}

p_internalreporting(){
    if $1 ; then
        printf "\x1b[32m[SUCCESS]\n\x1b[0m"
    else
        printf "\x1b[31m[ERROR]\n\x1b[0m"
    fi
}

gather_server_data(){
    echo "Gathering data from $server."
    sed -i "s/remote_temp_dir=.*/remote_temp_dir=${remote_temp_dir//\//\\/}/" ./resources/remote.sh
    e_ssh[$server]=false
    e_gathering[$server]=false
    if ssh $ssh_user@$server -i $ssh_certificate 'bash -s' < ./resources/remote.sh ; then
        e_scp[$server]=false
        echo Downloading data from $server
        scp -i $ssh_certificate $ssh_user@$server:$remote_temp_dir/hw $data/$server || e_scp[$server]=true
        scp -i $ssh_certificate $ssh_user@$server:$remote_temp_dir/pv $data/$server || e_scp[$server]=true
        scp -i $ssh_certificate $ssh_user@$server:$remote_temp_dir/vm $data/$server || e_scp[$server]=true
    else
        local err=$?
        if [[ $err -eq 0 ]] ; then
            pass
        elif [[ $err -eq 255 ]] ; then
            e_ssh[$server]=true
            e_gathering[$server]=true
        else
            e_gathering[$server]=true
        fi
        echo "SSH Error while connecting to $server."
    fi
}

build_report(){
    if ! ${e_scp[$server]} || $offline ; then
        echo "Building html file for $server."
        echo
        python3 ./resources/get_hyp_infos.py $data/$server > $html/$server.html
        err=$?
        e_python[$server]=false
        if [[ $err -eq 0 ]] ; then
            echo
            if [[ -s $html/$server.html ]] ; then
                echo "<tt><a href=\"./HTML/$server.html\" style=\"font-size: 20px\">$server</a></tt><br>" >> $report_directory/report.html
            else
                rm $html_file/$server.html
                e_python[$server]=true
            fi
        else
            e_python[$server]=true
            echo
        fi
    fi
}

to_csv(){
    if ! ${e_scp[$server]} || $offline ; then
        python3 ./resources/get_hyp_infos.py $data/$server > $html/$server.html
    fi
    err=$?
    e_python[$server]=false
    if [[ $err -eq 0 ]] ; then
        :
    fi
}

main(){
    # Errors management
    typeset -A e_ssh
    typeset -A e_gathering
    typeset -A e_scp
    typeset -A e_python

    # Parsing options :
    source ./config.sh
    local offline=false
    local csv=false
    while [[ $# -gt 0 ]] ; do
        case "$1" in
            # report directory 
            '-r' | '--report-directory')
                shift
                report_directory=$1
            ;;
            # comma separated server list
            '-s' | '--servers')
                shift
                servers=( $(echo $1 | tr ',' ' ') )
            ;;
            # ssh certificate
            '-i' | '--ssh-cert')
                shift
                ssh_certificate=$1
            ;;
            # ssh user
            '-u' | '--ssh-user')
                shift
                ssh_user=$1
            ;;
            # offline mode
            '-o' | '--offline')
                offline=true
            # to CSV
            '-c' | '--to-csv')
                csv=true
            ;;
            '-h' | '--help')
                p_help
                return 0
            ;;
            *)
                if [[ $arg != "" ]] ; then
                    printf "start.sh : Unknown argument : %s\n\n" "$1"
                    p_help
                    return 1
                fi
            ;;
        esac
        shift
    done

    # Building directories
    [[ -d $report_directory ]] || mkdir -p $report_directory || return 2
    [[ -d $html ]] || mkdir $html || return 2
    [[ -d $data ]] || mkdir $data || return 2
    
    # Opening HTML report file
    echo "<html>" > $report_directory/report.html

    # Main running logic
    for server in ${servers[@]} ; do
        [[ -d $data/$server ]] || mkdir $data/$server
        if ! $offline ; then
            gather_server_data
        fi
        if $csv ; then
            :
        else
            build_report
        fi
    done
    sed -i "s/remote_temp_dir=.*/remote_temp_dir=/" ./resources/remote.sh

    # Closing HTML report file
    echo "</html>" >> $report_directory/report.html

    # Internal reporting
    for server in ${servers[@]} ; do
        printf "\x1b[35m* %s\x1b[0m\n" "$server"
        if ! $offline ; then
            printf "SSH " "$server"
            p_internalreporting ${e_ssh[$server]}
            printf "data gathering " "$server"
            p_internalreporting ${e_gathering[$server]}
            printf "data downloading " "$server"
            p_internalreporting ${e_scp[$server]}
        fi
        printf "HTML page " "$server"
        p_internalreporting ${e_python[$server]}
        echo
    done
}

main "$@"