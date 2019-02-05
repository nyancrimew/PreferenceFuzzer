#
# Copyright (C) 2019 Lawnchair Launcher
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from enum import Enum
from ruamel import yaml
from utils.parse import parse_range
from hashlib import md5
import os
import click
import random
import utils.adb as adb

preferences = []

@click.command()
@click.argument('config', type=click.File())
@click.option('--path', default='gen', type=click.Path(), help='Directory to save any generated files to')
@click.option('--device', default=None, help='Serial number of the device to test on')
def main(config, path, device):
    # Load config file
    config = yaml.safe_load(config)

    for preference in config['preferences']: 
        preferences.append(Preference(preference))
    
    # Get XML string representation of the file
    prefs = _to_string(preferences)

    # Create output directory if it doesn't yet exist
    if not os.path.exists(path):
        os.mkdir(path)

    hash = md5(prefs.encode('utf8')).hexdigest()
    filename = f'{path}/{hash}-{config["name"]}.xml'
    if not os.path.exists(filename):
        # this combination is new, try it out
        with open(filename, 'w') as out:
            out.write(prefs)
        
        dev_filename = f'/sdcard/fuzzer/{hash}.xml'
        dev = adb.get_device(serial=device)
        # Push the preference to a temporary directory on the device
        dev.push(filename, dev_filename)
        # Force stop the app being tested
        _, stderr = dev.shell([
            'am',
            'force-stop',
            config['package']
        ])
        if stderr != None and len(stderr) > 0:
            click.echo(stderr, color='red', err=True)
            exit(-1)
        # Override preference file
        _, stderr = dev.shell([
            'run-as',
            config['package'],
            'cp',
            dev_filename,
            f'shared_prefs/{config["name"]}.xml'
        ])
        if stderr != None and len(stderr) > 0:
            click.echo(stderr, color='red', err=True)
            exit(-1)
        # Start specified activity
        _, stderr = dev.shell([
            'am',
            'start',
            '-n',
            f'{config["package"]}/{config["activity"]}'
        ])
        if stderr != None and len(stderr) > 0:
            click.echo(stderr, color='red', err=True)
            exit(-1)


def _to_string(preferences):
    s = f"<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n"
    s += _xmlStr('map', inner=preferences)
    return s
    

def _xmlStr(attr, name=None, value=None, inner=None):
    s = f'<{attr}'
    if name != None:
        s += f' name="{name}"'
    if value != None:
        s += f' value="{value}"'
    if inner == None or len(inner) == 0:
        s += ' /'
    s += '>'
    if inner != None and len(inner) > 0:
        if isinstance(inner, list):
            s += '\n'
            for line in inner:
                # hack to properly format indentation
                line = str(line).replace("\n", "\n\t")
                s += f'\t{line}\n'
        else:
            s += inner
        s += f'</{attr}>'
    return s

class Preference:
    def __init__(self, config):
        self.name = config['name']
        self.type = Type[config.get('type', 'string').upper()]
        if 'range' in config:
            self.values = parse_range(config['range'])
        elif 'values' in config:
            self.values = config['values']
        elif self.type == Type.BOOLEAN:
            self.values = ['true', 'false']
        if self.type == Type.SET:
            self.min = config.get(min, 0)
            self.max = config.get(max, -1)
            if self.max == -1:
                self.max = len(self.values)
    
    def __repr__(self):
        if self.type == Type.SET:
            # TODO: get rid of repetition
            val = random.choices(self.values, k=random.randint(self.min, self.max))
        else:
            val = random.choice(self.values)
        if self.type == Type.STRING:
            return _xmlStr(self.type.name.lower(), name=self.name, inner=val)
        elif self.type == Type.SET:
            return _xmlStr(self.type.name.lower(), name=self.name, inner=[_xmlStr('string', inner=v) for v in val ])
        else:
            return _xmlStr(self.type.name.lower(), name=self.name, value=str(val))

class Type(Enum):
    STRING = 0
    INT = 1
    BOOLEAN = 2
    FLOAT = 3
    SET = 4

if __name__ == '__main__':
    main()