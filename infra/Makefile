INVENTORY ?= inventory/production.yml

.PHONY: check ansible bootstrap verify

check:
	ansible-inventory -i $(INVENTORY) --graph
	ansible all -i $(INVENTORY) -m ping

ansible:
	ansible-playbook -i $(INVENTORY) ansible/site.yml

bootstrap:
	$(MAKE) check
	$(MAKE) ansible

verify:
	ansible rke2_servers -i $(INVENTORY) -a 'systemctl --failed'