#!/usr/bin/env python
# coding: utf-8

# # Python SDK for Cloud Native
# 
# 
# 

# ### Reference URL's
# 
# 

# #### https://docs.cloud.oracle.com/iaas/tools/oci-cli/latest/oci_cli_docs/index.html
# 
# #### https://github.com/oracle/learning-library/blob/master/oci-library/qloudable/OCI_CLI/OCI_CLI_HOL.md
# 
# #### Python SDK API 
# https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/api/landing.html
# ##### Core Services
# https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/api/core.html
# 
# #### Example Python SDK - showoci
# https://github.com/oracle/oci-python-sdk/tree/master/examples/showoci
# 

# # Initializations and Methods

# ## Global variables and Imports

# In[1]:


import os
import oci
import sys
import select
import time
import subprocess
import json ,  pprint
from IPython.display import display, Math, HTML, Markdown
display(HTML("<style>.container { width:100% !important; }</style>"))
display(HTML("<style>div.output_scroll { height: 70em; }</style>"))

# ## SSO Login initialization

# ### Session must first be authenticated in python oci console
# 

# #### Log into VCN first - not necessary
# #### (oracle-cli) C:\Users\kevin>oci session authenticate --region us-ashburn-1 --profile hpc-sso
#     Please switch to newly opened browser window to log in!
#     Completed browser authentication process!
# Enter the name of the profile you would like to create: hpc-sso
# Config written to: C:\Users\kevin\.oci\config
# 
#     Try out your newly created session credentials with the following example command:
# 
#     oci iam region list --config-file C:\Users\kevin\.oci\config --profile hpc-sso --auth security_token
# 
# 
# #### (oracle-cli) C:\Users\kevin>oci session refresh --profile hpc-sso
# Attempting to refresh token from https://auth.us-ashburn-1.oraclecloud.com/v1/authentication/refresh
# Successfully refreshed token
# 
# #### (oracle-cli) C:\Users\kevin>oci session validate --profile hpc-sso
# Session is valid until 2021-01-08 03:59:47
# 

# ### SSO config setup

# In[2]:


ssoProfile='oracle-sso'
ssoRegion='us-ashburn-1'
ssoProfileFlag = True
profiles = ['oracle-sso']
config = oci.config.from_file(profile_name=ssoProfile)
token_file = config['security_token_file']
token = None
with open(token_file, 'r') as f:
     token = f.read()

private_key = oci.signer.load_private_key_from_file(config['key_file'])

signer = oci.auth.signers.SecurityTokenSigner(token, private_key) 
client = oci.identity.IdentityClient({'region': ssoRegion}, signer=signer)
compts = client.list_compartments(compartment_id=config['tenancy']                                ,compartment_id_in_subtree=True)


network = oci.core.VirtualNetworkClient({'region': ssoRegion}, signer=signer)
# vcns = network.list_vcns({'region': ssoRegion}, signer=signer)
vcns = network.list_vcns(compartment_id="ocid1.compartment.oc1..aaaaaaaava4g6hckwuqohodh6bhsngbmvxfm2c4sst3fooejz3tmcepdvz7q")


# ### Test SSO config

# In[3]:


list_compartments_response = client.list_compartments(compartment_id=config['tenancy']                                        ,compartment_id_in_subtree=True)


comptList = (list_compartments_response.data)
for compt in comptList:
    #print(compt.name)
    if compt.name in 'DigitalExperience':
        break
        
regions = client.list_regions()
pprint.pprint(compt)


# # Reports

# ### Report Methods

# #### General Report Methods

# In[4]:


def formatCidrBlk(cidrBlk):
    # CIDR Blocks 
    cidridx = cidrBlk.index('/')
    cidr = cidrBlk[:cidridx]
    mask = cidrBlk[cidridx+1:]
    fmtCidr = ' \\textsf{' + cidr + '}_{' + mask + '} '
    return fmtCidr
display(Markdown('$$ '+(formatCidrBlk('10.2.0.0/2') + ' $$ '  )))


# #### Display Table of Compartments in this Report

# In[5]:


def showComptsTable(comptList):
    comptTableTitle = '$$\hspace {1mm} \\large {\\textbf{Compartments at a glance}}$$' 
    comptTable = ''
    comptTableTop = """
 \\begin{array}{|l|c|l|c|c|} \hline
 {\\small  \\textbf{Compartment} }  & {\\small  \\textbf{Status}}   & {\\small  \\textbf{Description}} 
      & \\overset{\\textbf{Spans}}{\\textbf{Regions}} & {\\small \\textbf{Network}}  
      & \\underset{\\small \\textbf{Instances}}{\\textbf{Compute}}  
      &  {\\small  \\textbf{Databases}}     
      &  {\\small  \\textbf{Storage}}   \\\[6pt] \hdashline
"""
    comptTableLine = "\\color{red}{\\textbf{ COMPT}} & {STATUS} & DESCR & {\\small REGIONS} & {\\small VCNS} "                      + " & {\\small COMPUTE}  & {\\small DATABASE} & {\\small STORAGE}  \\\[6pt] \hline "
    comptTableLines = []
    for compt in comptList:
        if compt.name not in [ 'kevin' ,'MainLab' , 'MathLab','QuantumLab','DigitalExperience']:
            continue
        tmpTableLine = comptTableLine
        tmpTableLine = tmpTableLine.replace('COMPT', compt.name  )
        if compt.lifecycle_state in 'ACTIVE':
            state = '\\color{green}{ \\Uparrow\\Uparrow } '
        else:
            state = '\\color{red}{ \\Downarrow\\Downarrow } '
        tmpTableLine = tmpTableLine.replace('STATUS',state)
        #        
        tmpTableLine = tmpTableLine.replace('DESCR', ' \\textsf{'  + compt.description  + '}  ' )
        #
        # Region determination
        # See if there are any VCN's associated with this compartment/region
        regions = []
        if not ssoProfileFlag:
            for profile in profiles:
                config = oci.config.from_file(profile_name=profile)
                # Add Region rows
                region=config['region']      
                print('Profile is: ',profile)
                # Get List of VCNs for this compartment
                network = oci.core.VirtualNetworkClient(config)
                vcns = network.list_vcns(compt.id)
                if vcns.data:
    #                 print('Compt - ' + compt.name + '  has vcns in region: ' + region  )
                    regions.append(region)
        else:
            network = oci.core.VirtualNetworkClient({'region': ssoRegion}, signer=signer)
            vcns = network.list_vcns(compt.id)
        # Begin Region Array for display within main array
        beginMatrix = "\\begin{array}{l} "
        newMatrix = beginMatrix
        for loopRegion in regions:
            rgn = loopRegion[:12]
            newMatrix = newMatrix + ' \\textsf {' +  rgn +   '} \\\[1pt]'
        regionMatrix = newMatrix + ' \end{array}\ '
        #
        tmpTableLine = tmpTableLine.replace('REGIONS', regionMatrix )
        # End Region

        beginMatrix = "\\begin{array}{c} "
        newMatrix = '  ';  newMatrix2 = '  '; newMatrix3 = '  '; newMatrix4 = '  '; newMatrix5 = '  '
        secMatrix = '  ';  vcnMatrix = '  ';  subnetMatrix = '  ' ; rtMatrix = '  '; dhcpOptMatrix = '  '
        vcnFoundFlag = False; subnetFoundFlag = False; secListFoundFlag = False; rtFoundFlag = False; dhcpOptFoundFlag = False
        
        for profile in profiles:
            config = oci.config.from_file(profile_name=profile)
            network = oci.core.VirtualNetworkClient({'region': ssoRegion}, signer=signer)
            print('-' + compt.name)
            vcns = network.list_vcns(compt.id)

#             print('Region', config['region'])
            
            if vcns.data:
                vcnFoundFlag = True
                for vcn in vcns.data:
                    print('vcn: ' + vcn.display_name)
                    newMatrix = newMatrix + ' \\textsf {' +  vcn.display_name +   '} \\\[1pt]'
                vcnMatrix = beginMatrix +  newMatrix + ' \end{array}\ '
            else:
                if not vcnFoundFlag:
                    vcnMatrix = ' {\\Tiny \\textsf{NO VCNs}}' 

            subnets = network.list_subnets(compt.id)
            
            if subnets.data:
                subnetFoundFlag = True
                for subnet in subnets.data:
#                     print('vcn: ' + subnet.display_name)
                    newMatrix2 = newMatrix2  + ' \\textsf {' +  subnet.display_name +   '} \\\[1pt]'
                subnetMatrix = beginMatrix +  newMatrix2 + ' \end{array}\ '
            else:
                if not subnetFoundFlag:
                    subnetMatrix = ' {\\Tiny \\textsf{NO Subnets}}'
                    
            secLists = network.list_security_lists(compt.id)
            
            if secLists.data:
                secListFoundFlag = True
                for secList in secLists.data:
                    newMatrix3 = newMatrix3  + ' \\Tiny \\textsf{' +  secList.display_name +   '} \\\[1pt]'
                secMatrix = beginMatrix +  newMatrix3 + ' \end{array}\ '
            else:
                if not secListFoundFlag:
                    secListMatrix = ' {\\small \\textsf{NO Security Lists}}'
                    
            rts = network.list_route_tables(compt.id)
            
            if rts.data:
                rtFoundFlag = True
                for rt in rts.data:
                    newMatrix4 = newMatrix4  + ' \\Tiny \\textsf{' +  rt.display_name +   '} \\\[1pt]'
                rtMatrix = beginMatrix +  newMatrix4 + ' \end{array}\ '
            else:
                if not rtFoundFlag:
                    rtMatrix = ' {\\small \\textsf{NO Route Tables}}'
                    
            dhcpOpts = network.list_dhcp_options(compt.id)
            
            if dhcpOpts.data:
                dhcpOptFoundFlag = True
                for dhcpOpt in dhcpOpts.data:
                    newMatrix5 = newMatrix5  + ' \\Tiny \\textsf{' +  dhcpOpt.display_name +   '} \\\[1pt]'
                dhcpOptMatrix = beginMatrix +  newMatrix5 + ' \end{array}\ '
            else:
                if not dhcpOptFoundFlag:
                    dhcpOptMatrix = ' {\\small \\textsf{NO DHCP Options}}'
                   
#             print('VCNMATRIX',vcnMatrix)
        # BEGIN Compute
        # 
#         print('COMPUTE')
        instanceMatrix = ' '; vnicMatrix = ' '
        newComputeMatrix =' '; newComputeMatrix2 =' '
        instanceFoundFlag = False; vnicFoundFlag = False

        for profile in profiles:
            config = oci.config.from_file(profile_name=profile)
            network = oci.core.VirtualNetworkClient({'region': ssoRegion}, signer=signer)
#             vcns = network.list_vcns(compt.id)
            print('Compt/Region' + compt.name + '/' +  config['region']  )

            compute = oci.core.ComputeClient({'region': ssoRegion}, signer=signer)
            instances = compute.list_instances(compt.id)
            if instances.data:
                instanceFoundFlag = True
                for instance in instances.data:
                    newComputeMatrix = newComputeMatrix  + ' \\textsf {' +  instance.display_name +   '} \\\[1pt]'
                instanceMatrix = beginMatrix +  newComputeMatrix + ' \end{array}\ '
            else:
                if not instanceFoundFlag:
                    instanceMatrix = ' {\\Tiny \\textsf{NO Instances}} '

            vnicAttchs = compute.list_vnic_attachments(compt.id)            
            if vnicAttchs.data:
                vnicFoundFlag = True
                for vnicAttch in vnicAttchs.data:
                    vnic = network.get_vnic(vnicAttch.vnic_id)
                    newComputeMatrix2 = newComputeMatrix2  + ' \\textsf {' +  vnic.data.display_name +   '} \\\[1pt]'
                vnicMatrix = beginMatrix +  newComputeMatrix2 + ' \end{array}\ '
            else:
                if not vnicFoundFlag:
                    vnicMatrix = ' {\\Tiny \\textsf{NO VNICs}} '                    

        # BEGIN DataBAse
        # 
#         print('DATABASE')
        dbaasMatrix = ' '; atpMatrix = ' '; adwMatrix = ' '
        newDatabaseMatrix =' '; newDatabaseMatrix2 =' '; newDatabaseMatrix3 =' '
        dbaasFoundFlag = False; atpFoundFlag = False; adwFoundFlag = False

        for profile in profiles:
            config = oci.config.from_file(profile_name=profile)
#             print('Compt/Region' + compt.name + '/' +  config['region']  )

            database_client = oci.database.DatabaseClient({'region': ssoRegion}, signer=signer)
    
            dbaasMatrix = ' {\\Tiny \\textsf{NO DBaaSs}} '   
    
            atps = database_client.list_autonomous_databases(compt.id)
            
            if atps.data:
                atpFoundFlag = True
                for atp in atps.data:
                    if atp.db_workload in 'OLTP':
                        newDatabaseMatrix2 = newDatabaseMatrix2  + ' \\textsf {' +  atp.display_name +   '} \\\[1pt]'
                atpMatrix = beginMatrix +  newDatabaseMatrix2 + ' \end{array}\ '
            else:
                if not atpFoundFlag:
                    atpMatrix = ' {\\Tiny \\textsf{NO ATPs}} '
                    
            if atps.data:
                adwFoundFlag = True
                for atp in atps.data:
                    if atp.db_workload in 'ADW':
                        newDatabaseMatrix3 = newDatabaseMatrix3  + ' \\textsf {' +  atp.display_name +   '} \\\[1pt]'
                adwMatrix = beginMatrix +  newDatabaseMatrix3 + ' \end{array}\ '
            else:
                if not adwFoundFlag:
                    adwMatrix = ' {\\Tiny \\textsf{NO ATPs}} '
                       
#         print('STORAGE')
        blockMatrix = ' '; fileSysMatrix = ' '; objectMatrix = ' '
        newStorageMatrix =' '; newStorageMatrix2 =' '; newStorageMatrix3 =' '
        blockFoundFlag = False; fileSysFoundFlag = False; objectFoundFlag = False

        for profile in profiles:
            config = oci.config.from_file(profile_name=profile)
            identity = oci.identity.IdentityClient({'region': ssoRegion}, signer=signer)
            availDomains = identity.list_availability_domains(compt.id)

            fsClient = oci.file_storage.FileStorageClient({'region': ssoRegion}, signer=signer)
            for availDomain in availDomains.data:
                fileSystems = fsClient.list_file_systems(compartment_id=compt.id,                                                         availability_domain=availDomain.name)

                if fileSystems.data:
                    fileSysFoundFlag = True
                    for fileSystem in fileSystems.data:
                        newStorageMatrix2 = newStorageMatrix2  + ' \\textsf {' +  fileSystem.display_name +   '} \\\[1pt]'
                    fileSysMatrix = beginMatrix +  newStorageMatrix2 + ' \end{array}\ '
                else:
                    if not fileSysFoundFlag:
                        fileSysMatrix = ' {\\Tiny \\textsf{NO ATPs}} '
            
            objStoreClient = oci.object_storage.ObjectStorageClient({'region': ssoRegion}, signer=signer)
            nameSpace = objStoreClient.get_namespace(compartment_id=compt.id)
            buckets = objStoreClient.list_buckets( namespace_name=nameSpace.data, compartment_id=compt.id)
            if buckets.data:
                objectFoundFlag = True
                for bucket in buckets.data:
                    newStorageMatrix3 = newStorageMatrix3  + ' \\textsf {' +  bucket.name +   '} \\\[1pt]'
                objectMatrix = beginMatrix +  newStorageMatrix3 + ' \end{array}\ '
            else:
                if not objectFoundFlag:
                    objectMatrix = ' {\\Tiny \\textsf{NO ATPs}} '
       
        storageMatrix = beginMatrix + ' \\overbrace{ ' + fileSysMatrix + ' }^{\\color{red}{\\textbf{File Systems}}} \\\[1pt] \\\ \\hdashline  \\\[1pt] '  
        storageMatrix = storageMatrix + ' \\overbrace{ '   + objectMatrix +  ' }^{\\color{red}{\\textbf{Object Storage Buckets}}} \\\[1pt] \\\ \\hdashline  \\\[1pt] '  
        storageMatrix = storageMatrix + ' \end{array}\   '                                  
     
        databaseMatrix = beginMatrix + ' \\overbrace{ '   + atpMatrix +  ' }^{\\color{red}{\\textbf{ATPs}}} \\\[1pt] \\\ \\hdashline  \\\[1pt] '  
        databaseMatrix = databaseMatrix + ' \\overbrace{ '   + adwMatrix +  ' }^{\\color{red}{\\textbf{ADWs}}} \\\[1pt] \\\ \\hdashline  \\\[1pt] '  
        databaseMatrix = databaseMatrix + ' \\overbrace{ '   + dbaasMatrix +  ' }^{\\color{red}{\\textbf{DBaaSs}}} \\\[1pt] \\\ \\hdashline  \\\[1pt] '  
        databaseMatrix = databaseMatrix + ' \end{array}\   '                                  
     
        computeMatrix = beginMatrix + ' \\overbrace{ '   + instanceMatrix +  ' }^{\\color{red}{\\textbf{Instances}}} \\\[1pt] \\\ \\hdashline  \\\[1pt] '  
        computeMatrix = computeMatrix + ' \\overbrace{ '   + vnicMatrix +  ' }^{\\color{red}{\\textbf{VNICs}}} \\\[1pt] \\\ \\hdashline  \\\[1pt] '  
        computeMatrix = computeMatrix + ' \end{array}\   '                                  
                
        networkMatrix = beginMatrix + ' \\overbrace{ '   + vcnMatrix +  ' }^{\\color{red}{\\textbf{VCNs}}} \\\[1pt] \\\ \\hdashline  \\\[1pt] '  
        networkMatrix = networkMatrix + ' \\overbrace{ '   + subnetMatrix +  ' }^{\\color{red}{\\textbf{SUBNETs}}} \\\[1pt] \\\  \\hdashline \\\[1pt]  '  
        networkMatrix = networkMatrix + ' \\overbrace{ '   + secMatrix +  ' }^{\\color{red}{\\textbf{SECURITY LISTs}}} \\\[1pt] \\\ \\hdashline \\\[1pt]  '  
        networkMatrix = networkMatrix + ' \\overbrace{ '   + rtMatrix +  ' }^{\\color{red}{\\textbf{ROUTE TABLEs}}} \\\[1pt] \\\ \\hdashline \\\[1pt]  ' 
        networkMatrix = networkMatrix + ' \\overbrace{ '   + dhcpOptMatrix +  ' }^{\\color{red}{\\textbf{DHCP OPTIONs}}} \\\[1pt] \\\ \\hdashline \\\[1pt]  ' 
        networkMatrix = networkMatrix + ' \end{array}\   '
#        
        tmpTableLine = tmpTableLine.replace('VCNS', networkMatrix )
        tmpTableLine = tmpTableLine.replace('COMPUTE', computeMatrix )
        tmpTableLine = tmpTableLine.replace('DATABASE', databaseMatrix )
        tmpTableLine = tmpTableLine.replace('STORAGE', storageMatrix)
        #
        comptTableLines.append(tmpTableLine)
    
    for loopTableLine in comptTableLines:
        comptTable = comptTable + loopTableLine
        break

    comptTable = comptTableTop + comptTable + " \end{array} "
#     print('COMPTTABLE',comptTable)
    display(Markdown(comptTableTitle))
    display(Markdown(comptTable))
    return

showComptsTable(comptList)


# In[ ]:




