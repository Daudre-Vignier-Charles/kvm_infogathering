remote_temp_dir=
ERR=$remote_temp_dir/err
[[ -d $remote_temp_dir ]] || mkdir $remote_temp_dir
echo "" >$ERR

# lshw
if ! type yum >/dev/null 2>&1 1>$ERR ; then
    yum install -y lshw 2>&1 1>>$ERR ;
fi
lshw -class system,network,storage,power,cpu,memory -xml 1>$remote_temp_dir/hw 2>>$ERR

# pvs
pvs -o pv_name,pv_size,pv_free --noheadings --nosuffix --units b --separator ',' 1>$remote_temp_dir/pv 2>>$ERR

# vm
echo "">$remote_temp_dir/vm
for vm in $(virsh list --name) ; do
    virsh dominfo $vm |
        grep "Name:\|CPU(s):\|State:\|Max memory:\|Autostart:" |
        sed "s/Max memory/Max_memory/" |
        awk '{ result = result ( NR==1 ? "" : ",") $2 } END{ print result }' >> $remote_temp_dir/vm 2>>$ERR
done