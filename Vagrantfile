# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/bionic64"
  config.vm.provision :shell, path: "deployment/bootstrap.sh"

  # Create a forwarded port mapping which allows access to a specific port
  config.vm.network "forwarded_port", guest: 8888, host: 8888

  config.vm.synced_folder "~/data/companies_house", "/vagrant_data"

  config.vm.provider "virtualbox" do |vb|
    # Display the VirtualBox GUI when booting the machine
    vb.gui = false

     # Customize the amount of memory on the VM:
    vb.memory = "4096"
  end
end
