#!/usr/bin/env python

import abc

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser


class InventoryFilter(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.config = ConfigParser(allow_no_value=True)

    @abc.abstractmethod
    def get_host_ips(self, topo):
        pass

    @abc.abstractmethod
    def get_inventory(self, topo, layout):
        pass

    def get_layout_hosts(self, inv):
        count = 0
        for host_group in inv['hosts']:
            count += host_group['count'] if 'count' in host_group else 1
        return count

    def get_layout_host_groups(self, inv):
        """
        get all the list of host groups in layout
        """
        host_groups = []
        for host in inv['hosts']:
            if "host_groups" in host:
                host_groups.extend(host["host_groups"])
        return list(set(host_groups))

    def add_sections(self, section_list):
        for section in section_list:
            self.config.add_section(section)
        # adding a default section all
        if "all" not in self.config.sections():
            self.config.add_section("all")

    def set_children(self, inv):
        if 'host_groups' not in inv.keys():
            return
        for host_group in inv['host_groups']:
            if "children" in inv['host_groups'][host_group]:
                self.config.add_section("{0}:children".format(host_group))
                for child in inv['host_groups'][host_group]['children']:
                    self.config.set("{0}:children".format(host_group), child)


    def set_vars(self, inv):
        if 'host_groups' not in inv.keys():
            return
        for host_group in inv['host_groups']:
            if "vars" in inv['host_groups'][host_group]:
                self.config.add_section("{0}:vars".format(host_group))
                for var in inv['host_groups'][host_group]['vars']:
                    grp_vars = inv['host_groups'][host_group]['vars'][var]
                    grp_vars = str(grp_vars)
                    self.config.set(host_group + ":" + "vars", var, grp_vars)

    def add_ips_to_groups(self, inven_hosts, layout):
        # create a ip to host mapping based on count
        ip_to_host = {}
        inven_hosts.reverse()
        for host_name in layout['hosts']:
            if 'count' in host_name.keys():
                count = host_name['count']
            else:
                count = 1
            host_list = []
            if count > len(inven_hosts):
                count = len(inven_hosts)
            for i in range(count, 0, -1):
                item = inven_hosts.pop()
                host_list.append(item)
            ip_to_host[host_name["name"]] = host_list
        # add ips to the respective host groups in inventory
        for host_name in layout['hosts']:
            host_ips = ip_to_host[host_name["name"]]
            for ip in host_ips:
                for host_group in host_name['host_groups']:
                    self.config.set(host_group, ip)
                    self.config.set("all", ip)

    def add_common_vars(self, host_groups, layout):
        # defaults common_vars to [] when they doesnot exist
        host_groups.append("all")
        common_vars = layout['vars'] if 'vars' in layout.keys() else []
        for group in host_groups:
            items = dict(self.config.items(group)).keys()
            self.config.remove_section(group)
            self.config.add_section(group)
            for item in items:
                host_string = item
                for var in common_vars:
                    if common_vars[var] == "__IP__":
                        host_string += " " + var + "=" + item
                    else:
                        host_string += " " + var + "=" + common_vars[var]
                self.config.set(group, host_string)
