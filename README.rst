Technical specifications - ** Xtender serial communication (SCOM) tool in python**
==================================================================================

Introduction
------------

In this document, you will find explanations about pyscom.py script, the way it works and its commands. Be aware that the functioning is quite different from the Scom.exe tool.
This projet was coded by a trainee.

Program global description
--------------------------

pyscom is a script developed with python 3.8.10. It allows to communicate with Studer Innotec Xcom-232i modules via a command line prompt. It enables reading and writing parameters or information values from Xtender series devices using various commands.

Note: in the rest of this document, the word "object" describes a parameter, or an information read or written on Xtender series devices. 
Their format can be found in the Scom technical documentation. You can download it from the Studer Website, under the "openstuder" download section : `Downloads | STUDER (studer-innotec.com) <https://studer-innotec.com/downloads/>`_.

Structure of a command
----------------------

The classic structure of the commands used by pyscom.py is the following

.. code::

  pyscom.py \-port \-bps \-verb my_command dst_addr object_type object_id property_id format


While writing a command, you first need to define the parameters used to establish a connexion to the Xcom-232i module.

Here are those three different parameters:

**--port**: Name of the port where the Xcom-232i is connected. Defined on "COM1" by default.

**--bps**: Baud rate in bits per second. To use th e Xcom-232i, this number can either be 38400 or 115200. It's defined to 38400 by default.
Note: The default transfer speed of the Xcom-232i is also 38400. You can modify it by using the configuration tool "xcom configurator V1.0.34". You can download it from the Studer Website: `Downloads | STUDER (studer-innotec.com) <https://studer-innotec.com/downloads/>`_.

**--verb**: Verbosity. This parameter isn't used to configure the connexion. It defines the level of details (number between 0 and 3 included) of the message displayed after executing a command. It's defined to 2 by default.


After declaring connexions parameters, you will need to define which command you're going to use and its corresponding parameters. Here are some examples available in pyscom.py.
*Reminder: you can use the command "pyscom.py -help" to obtain the list of the commands and their corresponding parameters.*

**read_property**: Allows to read information or parameters by communicating with the Xcom-232i module.

**write_property**: Allows to write parameters by communicating with the Xcom-232i module.

**test**: Allows to test your connexion with the Xcom-232i module.

**version**: Display in the command line prompt the version of the script.

"read_property" command
-----------------------

This command creates a request that will read the value of an info or a parameter from a Xtender range device. You can use the multi-info format to read multiple info using only one command.

"read_property" command's structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code::

    pyscom.py \-port \-bps \-verb read_property dst_addr object_type object_id property_id format \[property_data\]

**dst_addr**: defines the Xcom-232i request's destination address. The list of addresses can be found in appendix 9.1.

**object_type**: define the object's type id (user info or parameter) targeted by the request:

- 1: to read infos

- 2: to read parameters

- 10: to read multiple info using multi-info format

**object_id**: defines the object's id (user info or parameter) targeted by the request. To use multi-info format, the id must be defined to 10.

**property_id**: for the object's type 1 (info) and 10 (multi-info), property_id is always 1.

**format**: define object's data format (user info or parameter) that will be read. The format list can be found in annexe 9.2. To use the multi-info, this parameter has to be set to "byte_stream".

**[property_data]**: This optional parameter is only used with the multi-info format. It contains a group of object id and assembly id that will be process at the same time. This field's format is as the following: (object_id:assembly_id),(object_id:assembly_id),etc...

Examples
^^^^^^^^

Here are some examples for the read command:
Example to read info property {3000} "Battery voltage [Vdc]" on the Xtender 1:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 read_property 101 1 3000 1 float

Example to read info property {11000} "Battery voltage [Vdc]" on the VarioTrack 1:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 read_property 301 1 11000 1 float

Example to read info property {3055} "Relay aux 2 mode" on the Xtender 1:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 read_property 101 1 3055 1 short_enum

Example to read a couple of information using the multi-info format:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 read_property 501 10 1 1 byte_stream (3000:Average),(3080:Sum),(7000:master),(11000:Average),(11004:Sum),(15010:Sum)

Example to read a parameter type property {1138} "Battery charge current [Adc]" (float) on the Xtender 1:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 read_property 101 2 1138 5 float

Example to read a parameter type property {1206} "Start hour (AUX 1)" (int32) on the Xtender 1:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 read_property 101 2 1206 5 int32

Example to read a parameter type property {1125} "Charger allowed" (bool) on the Xtender 1:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 read_property 101 2 1125 5 bool

Example to read a parameter type property {1311} "Operating mode (AUX 2)" (long_enum) on the Xtender 1:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 read_property 101 2 1311 5 long_enum

Example to read a parameter type property {14002} "Configuration of PV modules (VS-120)" (long_enum) on the VarioString 1:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 read_property 701 2 14002 5 long_enum


"write_property" command
------------------------

This command creates a request that will write the value of a parameter from a Xtender series device.

"write_property" command's structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code::

    pyscom.py \-port \-bps \-verb write_property dst_addr object_type object_id property_id format [property_data]

**dst_addr**: defines the Xcom-232i request's destination address. The list of addresses can be found in annexes 9.1.

**object_type**: defines the object's type id (user info or parameter) targeted by the request. As only parameters can be modified, object_type will always be 2. 

**object_id**: defines the object's id (user info or parameter) targeted by the request.

**property_id**: what part of the parameter will be written:
- 5: to write in FLASH the parameter's value.
- 6: to write in FLASH the minimal parameter's value.
- 7: to write in FLASH the maximal parameter's value.
- 8: to write in FLASH the parameter's level.
- 13: to write in RAM the parameter's value. The amount of writing in flash is limited to 1000 cycle maximum. This is why it is necessary to write in RAM if you want to write multiple parameters at the same time.

**format**: defines object's data format (user info or parameter) that will be read. The format list can be found in annexes 

**property_data**: define the value that will be written.

Examples
^^^^^^^^

Here are some examples for the write command:

Example to write a parameter type property {1138} "Battery charge current [Adc]" (float) on every Xtender, in RAM:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 write_property 100 2 1138 13 float 25
..

Example to write a parameter type property {1138} "Battery charge current [Adc]" (float) on every Xtender, in FLASH:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 write_property 100 2 1138 5 float 25

Example to write a parameter type property {1206} "Start hour (AUX 1)" (int32) on the Xtender 1, in FLASH:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 write_property 100 2 1206 5 int32 480

Example to write a parameter type property {1287} "Restore factory settings" (int32) on every Xtender, in FLASH:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 write_property 100 2 1287 5 int32 1

Example to write a parameter type property {1125} "Charger allowed" (bool) on the Xtender 1, in FLASH:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 write_property 101 2 1125 5 bool 0

Example to write a parameter type property {1311} "Operating mode (AUX 2)" (long enum) on every Xtender, in FLASH:

.. code::

    py pyscom.py --port=COM3 --bps=38400 --verb=1 write_property 100 2 1311 5 long_enum 8


"test" command
--------------

This command is used to tests your connection with an Xcom-232i by scanning every opened port.

.. code::

    py pyscom.py test

This command has no need for parameters. *The parameters "--port", "--bps", "--verb" don't need to be defined either.

"version" command
-----------------

This command displays the version of the software.

.. code::

    py pyscom.py version

This command has no need for parameters. *The parameters "--port", "--bps", "--verb" don't need to be defined either*.

Annexes
^^^^^^^

.. list-table:: Destination address
   :widths: 10 50 40
   :header-rows: 1

   * - dst_addr
     - Devices
     - Remarks

   * - 0
     - Broadcast
     -
   * - 100
     - A virtual address to access all XTH, XTM and XTS
     - Reading info or parameters returns the value of the Xtender master (101)
   * - 101-109
     - Address of each XTH, XTM or XTS inverter
     - In the order of the Xtender indexes visible on the RCC
   * - 191-193
     - Virtual address to access properties on all inverters on a phase: 191 for L1, 192 for L2 and 193 for L3
     - A reading of info or parameter returns the value of the phase master
   * - 300
     - A virtual address to access all VarioTrack
     - Reading an info or parameter returns the value of the VarioTrack master (301)
   * - 301-315
     - Address of each VarioTrack
     - In the order of the VarioTrack indexes visible on the RCC
   * - 501
     - Xcom-232i
     - Alias for the gateway that the DTE uses to communicate (the Xcom-232i to which you speak with RS-232)
   * - 600
     - A virtual address to access all BSP
     - Reading an info or parameter returns the value of the BSP master (601)
   * - 601
     - BSP address
     -
   * - 700
     - A virtual address to access all VarioString
     - Reading an info or parameter returns the value of the VarioString master (701)
   * - 701-715
     - Address of each VarioString
     - In the order of the VarioString indexes visible on the RCC

..

.. list-table:: Datas format
   :widths: 20 80
   :header-rows: 1

   * - Name
     - Description

   * - BOOL
     - Binary data, 1 byte, 0 = false, 1 = true, other values are invalid
   * - SHORT_ENUM
     - A value that is part of an enumeration of possible values, represented by a 2-byte integer
   * - LONG_ENUM
     - A value that is part of an enumeration of possible values, represented by a 4-byte integer
   * - ERROR
     - Error code
   * - INT32
     - Integer value
   * - FLOAT
     - Float value
   * - STREAM
     - A stream a byte of arbitrary length

..

