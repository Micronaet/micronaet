#!/usr/bin/env ruby
require 'rubygems' 
require 'ooor' 
Ooor.new({:url => 'http://localhost:8069/xmlrpc', :database => 'Fiam601r', :username => 'admin', :password => 'cgp.fmsp6'}) 
MrpBom.print_uml()
