#!/usr/bin/python


__all__ = ['update_openerp']

import os
import shutil
import glob
import bzrlib.builtins
from bzrlib.plugins import launchpad
from bzrlib.branch import Branch
from bzrlib.errors import NotBranchError
from bzrlib.revisionspec import RevisionSpec

def run_cmd(cmdname, *args, **kwargs):
    f = getattr(bzrlib.builtins, 'cmd_' + cmdname)()
    if hasattr(f, '_setup_outf'):
        # old versions of bzr does not have this function   
        # this function must be called to avoid a exception in bzr code
        f._setup_outf()
    return f.run(*args, **kwargs)

_VERSIONS = ('4.2', '5.0', '6.0','trunk')
_DEFAULT_VERSION = '6.0'

def update_openerp(dest_dir, version=_DEFAULT_VERSION, lplogin=None, export=False, revision=None, verbose=False):
    """
        if lplogin == None -> make a branch instead of a checkout
        if export == True -> bzr export 
        if revision is provided, get the branches at this revision
            more information with:
                $> bzr help revisionspec
    """
    def log(msg):
        if verbose:
            print msg

    if version not in _VERSIONS:
        raise Exception('Unknown version')
    dest_dir = dest_dir or '.'

    branch = lplogin is None
    if branch:
        BASEURL = 'lp:'
    else:
        BASEURL = 'bzr+ssh://%s@bazaar.launchpad.net/' % (lplogin,)

    # for now, there is no 5.0-extra-addons -> use trunk instead
    extraversion = version == '5.0' and 'stable_5.0' or version
    communityversion = version == '5.0' and 'trunk' or version  
    webversion = version == '5.0' and '5.0' or version  

    bzr_repository = {
        'server': (BASEURL + '~openerp/openobject-server/' + version, True),
        'client': (BASEURL + '~openerp/openobject-client/' + version, True),
        'addons': (BASEURL + '~openerp/openobject-addons/' + version, True),
        'addons-extra': (BASEURL + '~openerp-commiter/openobject-addons/extra-' + extraversion, False),
        'addons-community': (BASEURL + '~openerp-community/openobject-addons/trunk-addons-community', False),
        'web': (BASEURL + '~openerp/openobject-client-web/' + webversion, True),
    }

    bzr_links = {
        'addons/*': 'server/bin/addons/',
    }

    if branch:
        cmd = {'new': lambda u, l, r: run_cmd('branch', u, l, revision=r),
               'update': lambda u, l, r: run_cmd('pull', u, directory=l, overwrite=True, revision=r),
        }
    else:
        cmd = {'new': lambda u, l, r: run_cmd('checkout', u, l, lightweight=True, revision=r),
               'update': lambda u, l, r: run_cmd('update', l), # no revision option :(
        }
    cmd['export'] = lambda u, l, r: run_cmd('export', l, u, revision=r)

    msg = "%(status)s %(type)s of %(from)s into %(to)s"

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    for local, (bzrdir, has_tags) in bzr_repository.items():
        local = os.path.join(dest_dir, local)
        typ = ['checkout', 'branch'][branch]
        if export:
            if os.path.exists(local):
                shutil.rmtree(local)
            status = 'export'
            typ = 'sources'
        else:
            try:
                b = Branch.open(local)
                # FIXME check that the current workingDirectory is a branch or a checkout
                status = 'update'
            except NotBranchError:
                status = 'new'
        
        frm = bzrdir
        rev = None
        if revision and (not revision.startswith('tag:') or has_tags):
            frm = '%s (%s)' % (bzrdir, revision)
            rev = RevisionSpec.from_string(revision)

        log(msg % {'status': status, 'type': typ, 'to': local, 'from': frm})
                
        cmd[status](bzrdir, local, rev and [rev] or None)

    # Doing symlinks
    log('(Re)Computing Symbolic links...')
    for src2,dest2 in bzr_links.items():
        src2 = os.path.join(dest_dir, src2)
        dest2 = os.path.join(dest_dir, dest2)
        for src in glob.glob(src2):
            dest = os.path.join(dest2, os.path.basename(src))
            if not os.path.isdir(dest):
                os.symlink(os.path.realpath(src), dest)

    log('='*79)
    log('Sources of OpenERP have been installed. If you develop new features,')
    log('you can get more information on how to contribute to the project here:')
    log('\thttp://test.openobject.com')
    log('='*79)

#
# Testing bzr send
#

if __name__ == '__main__':
    import optparse
    description = """Tool that allows you to get the last sources of openerp on launchpad.
It downloads all branches, and create symlinks for addons in the server. By
default, it loads the latest stable version.
"""
    parser = optparse.OptionParser(description=description, 
                                   usage="%prog [options] [directory]")
    parser.add_option('--checkout', dest='lplogin', help="Specify the launchpad login to make a checkout instead of a branch")
    parser.add_option('--export', dest='export', help='Make an export of the sources, instead of branches', action='store_true', default=False)
    parser.add_option('-v', dest="version", default=_DEFAULT_VERSION, type="choice", choices=_VERSIONS, help="Specify the version to take (trunk, 4.2, 5.0)")
    parser.add_option('-r', dest="revision", default=None, help="Specify the revision to take. (usefull to take a specific TAG or to specify a DATE)")
    parser.add_option('-q', '--quiet', dest='quiet', help='Suppress the output', action='store_true', default=False)
    opt, args = parser.parse_args()
    dest_dir = args and args[0] or '.'
    update_openerp(dest_dir, opt.version, opt.lplogin, opt.export, opt.revision, not opt.quiet)

