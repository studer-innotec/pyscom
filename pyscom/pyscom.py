import platform                     
import struct                       
import click                        
import serial                       
from dataclasses import dataclass   
from typing import Union            
import math                         
import re                           
import datetime




# Dataclass used to store frames
@dataclass
class Frame:
    src_addr : int
    dest_addr : int
    data_length : int
    object_type : int
    object_id : int
    property_id : int
    property_data : Union[int, float, bool, str]
    full_frame : str


debug = False    # State that define outputs for debugging purposes


# Used to define sub commands
@click.group()
@click.option('--port', default="COM1", help="The serial port's name [default: COM1]")                     
@click.option('--bps', type=float, default=38400, help="The baudrate supported by the xcom-232 (38400 or 115200)")  
@click.option('--verb', type=int, default=2, help="""The level of quantity of informations returned       
                    0: quiet, value only (12.3)              
                    1: all field of the response on one line              
                    2: full description on multiple lines [default]              
                    3: same as 2, but with debug information""")
@click.pass_context
def commands(ctx, port, bps, verb):
    ctx.obj = {}
    params = [port, bps, verb]
    ctx.obj['params'] = params  # Pass the parameters to the context


#Display current version informations
@commands.command(name="version", help="Display current version informations")
def version():
    print("script version: 1.0.8")


# Try to find a connection and test it
@commands.command(name="test", help="try to find a connection and test it")
@click.pass_context
def test(ctx):
    bps = ctx.obj['params'][1]
    output_message = "scan port: "  # The message that will be be printed in the command invite
    can_communicate = False         # Flag to see if the port can cmmunicate with the XT

    for i in range(1, 21):
        if platform.system() == "Windows":
            port_name = f"COM{i}"
        elif platform.system() == "Linux":
            port_name = f"/dev/ttyUSB{i}"
        output_message += port_name + " "
        # Check if the port can connect to the XT
        if can_open_port(port_name, bps):
            print(output_message + "\n")
            print(f"{port_name} opened with success, trying to communicate with the target...")
            for dst_id in range(100, 101):
                # Send and try to recieve data from the XT
                tx_frame = encode_read_request(1, dst_id, 1, 3000, 1)
                rx_frame = send_frame(tx_frame, port_name, 38400)
                # Check if it has recieved data from the XT
                if rx_frame:
                    can_communicate = True
                    frame = decode_response_frame(rx_frame, "float", True)
                    value = round(frame.property_data, 2)
                    print(f"inverter addr_id={frame.src_addr} with v_bat={value} detected")
                output_message = "scan port: "
             # If every requests failed, display an error message
            if not can_communicate:
                print(f"Port {port_name} was not able to communicate with the target")
    print(output_message + "\n")
    

# Read the given property of the given device
@commands.command(name="read_property", help="read an arbitrary property of an object\nread_property for multi-info format: (userRef:infoAssembly),(userRef:infoAssembly),etc...")
@click.argument('dst_addr', type=int)       # Destination address
@click.argument('object_type', type=int)    # The object's type id
@click.argument('object_id', type=int)      # The object's id
@click.argument('property_id', type=int)    # The property's id
@click.argument('format', type=str)         # The format the returned data will be displayed
@click.argument('property_data', required=False)    # The property's id
@click.pass_context                         # This command has access to the context
def read_property(ctx, dst_addr, object_type, object_id, property_id, format, property_data):
    validate_parameters(ctx) # Validate the command's parameters

    if debug : print(" --- CMD read_property")  

    port = ctx.obj['params'][0] 
    bps = ctx.obj['params'][1]

    if debug:     
        print("\t********** debug data start **********")
        print("\tport\t\t\t: ", port)
        print("\tbps\t\t\t: ", bps)
        print("\tdst_addr\t\t: ", dst_addr)
        print("\tobject_type\t: ", object_type)
        print("\tobject_id\t\t: ", object_id)
        print("\tproperty_id\t: ", property_id)
        print("\tformat\t\t: ", format)
        print("\tproperty_data\t ", property_data)
        print("\t********** debug data end ***********")

    # Create the transmitted frame and get the returned frame
    tx_frame = encode_read_request(1, dst_addr, object_type, object_id, property_id, property_data)
    rx_frame = send_frame(tx_frame, port, bps)

    if debug: 
        print("tx_frame_raw :\t",tx_frame)
        print("rx_frame_raw :\t",rx_frame)

    if rx_frame:
        # Turn both frame to the dataclass "Frame"
        tx_frame = decode_request_frame(tx_frame, format, True)
        rx_frame = decode_response_frame(rx_frame, format, True)

        if debug: 
            print("\t********** debug data start **********")
            print("\ttx_frame : ",tx_frame)
            print("\trx_frame : ",rx_frame)
            print("\t********** debug data end ***********")

        # Show the resulting message
        show_resume(tx_frame, rx_frame, format, ctx)
    else:
        print("This requests has return nothing. Please check the syntaxe or the power of your installation")


# Write the given property of the given device
@commands.command(name="write_property", help="write an arbitrary property of an object")
@click.argument('dst_addr', type=int)                               # Destination address
@click.argument('object_type', type=int)                            # The object's type id
@click.argument('object_id', type=int)                              # The object's id
@click.argument('property_id', type=int)                            # The property's id
@click.argument('format', type=str)                                 # The format the returned data will be displayed
@click.argument('property_data') # The value that will be written
@click.pass_context                                                 # This command has access to the context
def write_property(ctx, dst_addr, object_type, object_id, property_id, property_data, format):
    validate_parameters(ctx) # Validate the command's parameters

    if debug : print(" --- CMD: write_property") 

    port = ctx.obj['params'][0] 
    bps = ctx.obj['params'][1]

    # Create the transmitted frame and get the returned frame
    tx_frame = encode_write_request(1, dst_addr, object_type, object_id, property_id, property_data, format)
    rx_frame = send_frame(tx_frame, port, bps)

    if rx_frame:
        # Turn both frame to the dataclass "Frame"
        tx_frame = decode_request_frame(tx_frame, format, False)
        rx_frame = decode_response_frame(rx_frame, format, False)

        # Show the resulting message
        show_resume(tx_frame, rx_frame, format, ctx)
    else:
        print("This requests has return nothing. Please check the syntaxe or the power of your installation")


# Make sure that the port name is valid
def set_port(port):
    """Make sure that the port name is valid"""

    if debug : print("   --- set_port")  

    global c_port
    for i in range(0, 21):
        if port == f"COM{i}" or port == f"/dev/ttyUSB{i}":
            c_port = port


# Make sure that the baud rate is valid
def set_bps(bps):
    """Make sure that the baud rate is valid"""

    if debug : print("   --- set_bps")

    global c_bps
    if bps == 38400 or bps == 115200:
        c_bps = bps


# Make sure that the verbose level is valid
def set_verb(verb):
    """Make sure that the verbose level is valid"""

    if debug : print("   --- set_verb")   

    global c_verb
    if verb in range(0, 4):
        c_verb = verb


# Make sure that the parameters are valid
def validate_parameters(ctx):
    """Make sure that the parameters are valid"""

    if debug : print(" --- validate_parameters")

    set_port(ctx.obj['params'][0])          # Validate the port name
    set_bps(ctx.obj['params'][1])           # Validate the baud rate
    set_verb(ctx.obj['params'][2])          # Validate the verbose level


# Send the given frame the the XT from the COM port
def send_frame(tx_frame, port_name, baudrate):
    """Send the given frame the the XT from the COM port"""

    if debug : print(" --- send_frame")
    
    # Open the serial communication on the given port
    ser = serial.serial_for_url(url=port_name, baudrate=baudrate, timeout=3, write_timeout=3, bytesize=8, parity=serial.PARITY_EVEN, stopbits=1)
    # Send the frame in parameter to the XT
    ser.write(bytes.fromhex(tx_frame))
    
    rx_frame = ""

    # Will read the returned frame until it's empty
    while (True):
        data = ser.read()   # Read the frame returned
        if data != b'':
            rx_frame += data.hex()
        else:
            break

    ser.close()
    # Return a string of the frame of HEX values
    return rx_frame


# Build the frame of HEX values from the command's parameters to use the "read_property" service
def encode_read_request(src_addr, dst_addr, object_type, object_id, property_id, property_data=None):    
    """Build the frame of HEX values from the command's parameters to use the "read_property" service"""

    if debug :
        print(" --- encode_read_request")
        print("\t********** debug data start **********")
        print("\tproperty_data : ", property_data)                
        print("\t********** debug data end ************")

    frame_request = ""
    
    hex_start = 'aa'            # Start byte is always "AA"
    hex_frame_flags = '00'
    hex_src_addr = convert_int32_to_hex(src_addr, 4)
    hex_dst_addr = convert_int32_to_hex(dst_addr, 4)
    hex_service_flags = '00'    # Specify that it's not a response nor an error
    hex_service_id = '01'       # Specify that the frame use the "read_property" service
    hex_object_type = convert_int32_to_hex(object_type, 2)
    hex_object_id = convert_int32_to_hex(object_id, 4)
    hex_property_id = convert_int32_to_hex(property_id, 2)
    # Calculate the number of byte in the frame_data
    data_size = int((len(hex_service_flags) + len(hex_service_id) + len(hex_object_type) + len(hex_object_id) + len(hex_property_id)) / 2)
    
    if debug :
        print("\t********** debug data start **********")
        print("\tproperty_data : ", property_data)                
        print("\t********** debug data end ************")

    if property_data is not None:
        hex_property_data = encode_multi_info(property_data)
        data_size += int((len(hex_property_data) / 2))
    hex_data_size = convert_int32_to_hex(data_size, 2)
    # Put together the bytes use to calculate the header and data checksum
    header_hex = hex_frame_flags + hex_src_addr + hex_dst_addr + hex_data_size    

    data_hex = hex_service_flags + hex_service_id + hex_object_type + hex_object_id + hex_property_id
    if property_data is not None:
        data_hex += hex_property_data

    # Calculate both checksum
    hex_header_checksum = calc_checksum(header_hex, len(header_hex))
    hex_data_checksum = calc_checksum(data_hex, len(data_hex))
    
    # Put together all the string of HEX value to build the frame
    frame_request = hex_start + hex_frame_flags + hex_src_addr + hex_dst_addr + hex_data_size + hex_header_checksum.to_bytes(2, byteorder='big').hex()
    frame_request += hex_service_flags + hex_service_id + hex_object_type + hex_object_id + hex_property_id
    if property_data is not None:
        frame_request += hex_property_data
    frame_request += hex_data_checksum.to_bytes(2, byteorder='big').hex()

    return frame_request


# Build the frame of HEX values from the command's parameters to use the "write_property" service
def encode_write_request(src_addr, dst_addr, object_type, object_id, property_id, property_data, format):
    """Build the frame of HEX values from the command's parameters to use the "write_property" service"""
    
    if debug : print(" --- encode_write_request")

    frame_request = ""
    
    hex_start = 'aa'            # Start byte is always "AA"
    hex_frame_flags = '00'
    hex_src_addr = convert_int32_to_hex(src_addr, 4)
    hex_dst_addr = convert_int32_to_hex(dst_addr, 4)
    hex_service_flags = '00'    # Specify that it's not a response nor an error
    hex_service_id = '02'       # Specify that the frame use the "write_property" service
    hex_object_type = convert_int32_to_hex(object_type, 2)
    hex_object_id = convert_int32_to_hex(object_id, 4)
    hex_property_id = convert_int32_to_hex(property_id, 2)    
    hex_property_data = convert_to_hex_from_format(property_data, format)

    # Calculate the number of byte in the frame_data
    data_size = int((len(hex_service_flags) + len(hex_service_id) + len(hex_object_type) + len(hex_object_id) + len(hex_property_id) + len(hex_property_data)) / 2)
    hex_data_size = convert_int32_to_hex(data_size, 2)
    # Put together the bytes use to calculate the header and data checksum
    header_hex = hex_frame_flags + hex_src_addr + hex_dst_addr + hex_data_size    
    data_hex = hex_service_flags + hex_service_id + hex_object_type + hex_object_id + hex_property_id + hex_property_data
    
    # Calculate both checksum
    hex_header_checksum = calc_checksum(header_hex, len(header_hex))
    hex_data_checksum = calc_checksum(data_hex, len(data_hex))    

    # Put together all the string of HEX value to build the frame
    frame_request = hex_start + hex_frame_flags + hex_src_addr + hex_dst_addr + hex_data_size + str(hex(hex_header_checksum))[2:]
    frame_request += hex_service_flags + hex_service_id + hex_object_type + hex_object_id + hex_property_id + hex_property_data + str(hex(hex_data_checksum))[2:]

    return frame_request


# Convert multi-info parameter into their HEX value
def encode_multi_info(original_str):
    
    """Convert multi-info parameter into their HEX value"""

    if debug :
        print(" --- encode_multi_info")
        print("\t********** debug data start **********")
        print("\tencode original string passed : ",original_str)
        print("\t********** debug data end ***********")

    hex_data = ""
    # Delete all ( ) in the string passed as parameter
    original_str = original_str.replace("(", "").replace(")", "")

    # Split the string at ":" and "," to get list with only datas
    all_datas = re.split(r'[:,]', original_str)

    # Browse the previously initiated list
    try:
        for index, data in enumerate(all_datas):
            # Assemblies are placed every two items of the list. 
            if index % 2 == 1:
                # Convert Assembly text to hex
                hex_data += convert_int32_to_hex(convert_assembly_to_id(data), 1)
            else:
                hex_data += convert_int32_to_hex(int(data), 2)
        return hex_data
    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        exit()


# Turn the returned frame into an instance of the "Frame" dataclass
def decode_response_frame(frame, format, is_read):  
    
    """Turn the returned frame into an instance of the "Frame" dataclass"""

    if debug : print(" --- decode_response_frame")

    format = format.lower()    
    # Decode in the right format the part of the frame that correspond each variable
    src_addr = struct.unpack("<i", bytes.fromhex(frame[4:12].zfill(8)))[0]
    dest_addr = struct.unpack("<i", bytes.fromhex(frame[12:20].zfill(8)))[0]
    data_length = struct.unpack("<h", bytes.fromhex(frame[20:24].zfill(4)))[0]
    object_type = struct.unpack("<h", bytes.fromhex(frame[32:36].zfill(4)))[0]
    object_id = struct.unpack("<i", bytes.fromhex(frame[36:44].zfill(8)))[0]
    property_id = struct.unpack("<h", bytes.fromhex(frame[44:48].zfill(4)))[0]

    # This will decode the property data in the given format
    if check_format(format):
        # Decode for bool format
        try:
            if format == "bool":
                data_bool = struct.unpack("<b", bytes.fromhex(frame[48:50]))[0]
                property_data = None
                if data_bool == 0:
                    property_data = False
                elif data_bool == 1:
                    property_data = True
            # Decode for short_enum format
            elif format == "short_enum" or format == "long_enum" and not is_read or format == "int32" and not is_read:
                property_data = struct.unpack("<h", bytes.fromhex(frame[48:(48 + (data_length - 10) * 2)].zfill(4)))[0]
            # Decode for long_enum format
            elif format == "long_enum" and is_read or format == "int32" and is_read:
                property_data = struct.unpack("<i", bytes.fromhex(frame[48:(48 + (data_length - 10) * 2)].zfill(4)))[0]
            # Decode for float format
            elif format == "float":
                property_data = struct.unpack("<f", bytes.fromhex(frame[48:(48 + (data_length - 10) * 2)].zfill(8)))[0]
            # Decode for byte_stream format
            elif format == "byte_stream":
                property_data = decode_byte_stream(frame[48:(48 + (data_length - 10) * 2)])
            
            return Frame(src_addr, dest_addr, data_length - 10, object_type, object_id, property_id, property_data, frame)
        except Exception as e:
            print(e.message if hasattr(e, 'message') else e)
            exit()

    
# Turn the sended frame into an instance of the "Frame" dataclass
def decode_request_frame(frame, format, read_request):
    
    """Turn the sended frame into an instance of the "Frame" dataclass"""

    if debug : print(" --- decode_request_frame")

    # Decode in the right format the part of the frame that correspond each variable
    src_addr = struct.unpack("<i", bytes.fromhex(frame[4:12]))[0]
    dest_addr = struct.unpack("<i", bytes.fromhex(frame[12:20]))[0]
    data_length = struct.unpack("<h", bytes.fromhex(frame[20:24]))[0]
    object_type = struct.unpack("<h", bytes.fromhex(frame[32:36]))[0]
    object_id = struct.unpack("<i", bytes.fromhex(frame[36:44]))[0]
    property_id = struct.unpack("<h", bytes.fromhex(frame[44:48]))[0]
    # A frame using the "read_property" service isn't supposed to have "property_data" bytes
    if not read_request:
        try:
            if check_format(format):
                # Decode for bool format
                if format == "bool":
                    data_bool = struct.unpack("<b", bytes.fromhex(frame[48:50]))[0]
                    property_data = None
                    if data_bool == 0:
                        property_data = False
                    elif data_bool == 1:
                        property_data = True
                # Decode for enum format
                elif format == "short_enum":
                    property_data = struct.unpack("<h", bytes.fromhex(frame[48:(48 + (data_length - 10) * 2)].zfill(4)))[0]
                elif format == "long_enum":
                    property_data = struct.unpack("<i", bytes.fromhex(frame[48:(48 + (data_length - 10) * 2)].zfill(4)))[0]
                # Decode for float format
                elif format == "float":
                    property_data = struct.unpack("<f", bytes.fromhex(frame[48:(48 + (data_length - 10) * 2)].zfill(8)))[0]
                # Decode for int format    
                elif format == "int32":
                    property_data = struct.unpack("<i", bytes.fromhex(frame[48:(48 + (data_length - 10) * 2)].zfill(8)))[0]
        except Exception as e:
            print(e.message if hasattr(e, 'message') else e)
            exit()
    else: 
        # Nullify the property_data if it isn't a write request
        property_data = None

    return Frame(src_addr, dest_addr, data_length - 10, object_type, object_id, property_id, property_data, frame)


# Decode the response's byte_stream to a formated string of it's data
def decode_byte_stream(byte_stream):
    
    """Decode the response's byte_stream to a formated string of it's data"""

    if debug : print(" --- decode_byte_stream")

    # The 16th first characters (8th first bytes) don't correspond to the datas and their values
    result_data = byte_stream[16:]
    # Split the remaining characters every 14 characters (length of a data)
    all_data_splited = [result_data[i:i+14] for i in range(0, len(result_data), 14)]

    returned_string = "\n"
    for datas in all_data_splited:
        hex_info_ref = struct.unpack("<h", bytes.fromhex(datas[0:4]))[0]
        hex_aggreg = struct.unpack(">h", bytes.fromhex(datas[4:6].zfill(4)))[0]
        hex_value = struct.unpack("<f", bytes.fromhex(datas[6:14].zfill(8)))[0]
        returned_string += f"Information reference: {hex_info_ref}\t| Aggregation: {convert_id_to_assembly(hex_aggreg)}\t| Value : {hex_value}\n"

    return returned_string


# Print in the command invite the resulting message of the communication
def show_resume(tx_frame, rx_frame, format, ctx):
    
    """Print in the command invite the resulting message of the communication"""

    if debug : print(" --- show_resume")

    # Look if the sended frame use the "read_property" service
    is_reading = is_txFrame_read(tx_frame.full_frame)


    port = ctx.obj['params'][0]
    verb = ctx.obj['params'][2]
    
    # Simply define a separator character for the data's text
    # depending on the verbose level
    if verb==1:
        separator_char = " "
    elif verb>=2:
        separator_char = " \n"
        
    show_tx_info = ""
    show_rx_info = ""

    # That bit of text and both frame are only showed with a verbose level of 3
    if verb==3:        
        show_tx_info += "send property request: \n"
        show_rx_info += "response: \n"
        show_tx_frame = get_hex_resume(tx_frame.full_frame)
        show_rx_frame = get_hex_resume(rx_frame.full_frame)

    # Doesn't show the property_data of the sended frame if it's empty. Otherwise it show the hex value of it
    property_data = "" if tx_frame.property_data is None else get_hex_resume(convert_to_hex_from_format(tx_frame.property_data, format))

    # It only show the sended frame information on verbose level 1 and above
    if verb >= 1:
        show_tx_info += f"device_addr={tx_frame.dest_addr}{separator_char}object_type={tx_frame.object_type}{separator_char}object_id={tx_frame.object_id}{separator_char}"
        show_tx_info += f"property_id={tx_frame.property_id}{separator_char}length={tx_frame.data_length}{separator_char}data={separator_char}{property_data} \n"
    
    try:
        # Doesn't show the property_data of the returned frame if it's empty. Otherwise it show it's value
        property_data = "" if rx_frame.property_data is None else rx_frame.property_data
    
    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        exit()
    

    # Check if the returned frame don't contain any error
    if not check_frame_has_error(rx_frame.full_frame):

        if format.lower() == "byte_stream" and verb == 3:
            print(get_byte_stream_context(rx_frame.full_frame[48:(48 + (rx_frame.data_length - 10) * 2)]))

        #Only show the property data if the verbose level is on 0
        if verb >= 1:
            show_rx_info += f"device_addr={rx_frame.src_addr}{separator_char}object_type={rx_frame.object_type}{separator_char}object_id={rx_frame.object_id}{separator_char}"
            show_rx_info += f"property_id={rx_frame.property_id}{separator_char}length={rx_frame.data_length}{separator_char}data={property_data} \n"
        else:
            show_rx_info = str(property_data)
    else:
        #Show the error's name and description
        error = get_error(rx_frame.full_frame)
        show_rx_info += f"an error occured: {error[0]} \n"
        show_rx_info += error[1] + "\n"
    # The first line is different depending on the service used by the sended frame
    if is_reading or check_frame_has_error(rx_frame.full_frame):
        print(f"read info ({format.lower()}) - {show_rx_info}")
    else:
        print(f"write parameter ({format.lower()})")
    # Only show debug information on verbose level 3
    if verb == 3:
        print(f"\ndebug: verbose_level={verb}\ndebug: port={port}\n")
    # Only show sended frame datas on verbose level 2 and above
    if verb>=2:
        print(show_tx_info)
    # Only show both frames content on verbose level 3
    if verb == 3:
        print("debug: tx bytes")
        print(show_tx_frame)    
        print("debug: rx bytes")
        print(show_rx_frame)


# Format an HEX value into a table of 10 bytes each line
def get_hex_resume(frame):
    
    """Format an HEX value into a table of 10 bytes each line"""

    if debug : print(" --- get_hex_resume") 

    # Calculate table's lines number
    rows_count = math.ceil(len(frame) / 20)
    

    # Split the string of HEX value every two character (every byte)
    # and format it the make a table of {rows_count} lines
    trame_resume = ""
    split_tx_frame = [frame[i:i+2] for i in range(0, len(frame), 2)]
    for row in range(0, rows_count):
        trame_resume += f"{row}0|".zfill(len(str(rows_count)) + 3)
        for col in range(0, 10):  
            if split_tx_frame:
                trame_resume += f" {split_tx_frame[0].upper()}"
                del split_tx_frame[0]
        trame_resume += "\n"
    return trame_resume


# Return the error's name and description generated in the given frame
def get_error(frame):
    
    """Return the error's name and description generated in the given frame\n
    error[0]: Error name (e.g: READ_PROPERTY_FAILED)\n
    error[1]: Error description (e.g: reading is possible, but failed)\n"""

    if debug : print(" --- read_propertyget_error")

    # It contains every existing error code with it's name and description 
    all_errors =    {
                        "0001": ["INVALID_FRAME", "malformed frame"],
                        "0002": ["DEVICE_NOT_FOUND", "wrong dst_addr field"],
                        "0003": ["RESPONSE_TIMEOUT", "no response of the server"],
                        "0011": ["SERVICE_NOT_SUPPORTED", "wrong service_id field"],
                        "0012": ["INVALID_SERVICE_ARGUMENT", "wrong service_data"],
                        "0013": ["SCOM_ERROR_GATEWAY_BUSY", "gateway (for example XCOM-232i) busy"],
                        "0021": ["TYPE_NOT_SUPPORTED", "the object_type requested doesn't exist"],
                        "0022": ["OBJECT_ID_NOT_FOUND", "no object with this object_id was found"],
                        "0023": ["PROPERTY_NOT_SUPPORTED", "the property identified by property_id doesn't exist"],
                        "0024": ["INVALID_DATA_LENGTH", "the field property_data has an invalid number of bytes"],
                        "0025": ["PROPERTY_IS_READ_ONLY", "a writing to this property is not allowed"],
                        "0026": ["INVALID_DATA", "this value is impossible for this property"],
                        "0027": ["DATA_TOO_SMALL", "the value is below the minimum limit"],
                        "0028": ["DATA_TOO_BIG", "the value is above the maximum limit"],
                        "0029": ["WRITE_PROPERTY_FAILED", "writing is possible, but failed"],
                        "002A": ["READ_PROPERTY_FAILED", "reading is possible, but failed"],
                        "002B": ["ACCESS_DENIED", "insufficient user access"],
                        "002C": ["SCOM_ERROR_OBJECT_NOT_SUPPORTED", "this object id, through existant, is not supported by the current implementation of the gateway"],
                        "002D": ["SCOM_ERROR_MULTICAST_READ_NOT_SUPPORTED", "Read operation is not supported when used on multicast adresses."],
                        "002E": ["OBJECT_PROPERTY_INVALID", "During a file transfer, the use of this property was unexpected"],
                        "002F": ["FILE_OR_DIR_NOT_PRESENT", "Attempt to download a file not present on the sd card"],
                        "0030": ["FILE_CORRUPTED", "A read error ocurred during the download of a file"],
                        "0081": ["INVALID_SHELL_ARG", "the command line tool used received the wrong arguments"]
                    }
    # Find the error code (in HEX) in the frame
    error_code = frame[48:52][2:] + frame[48:52][:2]    
    # Browse the "all_errors" dict and try to match 
    # the error code from the given frame and
    # one of the possible error code. 
    # If there's a match, it return the error's name and description
    for error in all_errors:
        if error.upper() == error_code.upper():
            return all_errors[error]


# Decode the response's byte_stream to a formated string of it's data
def get_byte_stream_context(byte_stream):
    
    """Decode the response's byte_stream to a formated string of it's data"""

    if debug : print(" --- get_byte_stream_context ")

    # The 16th first characters (8th first bytes) don't correspond to the datas and their values
    result_data = byte_stream[:16]
    # The 8th first character contains the installation information
    context_bytes = result_data[:8]
    # The 8th last character contains the installation time
    time_bytes = result_data[8:]

    # Convert the datetime posix bytes to a datetime
    datetime_posix = datetime.datetime.fromtimestamp(int(struct.unpack('<i', bytes.fromhex(time_bytes))[0])) 

    # Get the first and second bit of the installation's informations
    fst_context_byte = [context_bytes[i:i+2] for i in range(0, len(context_bytes), 2)][0]
    snd_context_byte = [context_bytes[i:i+2] for i in range(0, len(context_bytes), 2)][1]

    byte_value = int(fst_context_byte, 16)      # Convert hex string of the first byte to integer
    bit_string = format(byte_value, '08b')      # Convert int to binary string
    fst_bits = [char for char in bit_string]    # Convert bits string into a list
    
    #the 4 LSB are the current version
    xcom_version = int(byte_value & 0b00001111)

    byte_value = int(snd_context_byte, 16)      # Convert hex string of the second byte to integer
    bit_string = format(byte_value, '08b')      # Convert int to binary string
    snd_bits = [char for char in bit_string]    # Convert bits string into a list
    
    # Convert the value of bit to a corresponding boolean
    for index in range(0, 8):
        fst_bits[index] = True if int(fst_bits[index]) == 1 else False
        snd_bits[index] = True if int(snd_bits[index]) == 1 else False

    if fst_bits[4]:
        xcom = "Xcom-GSM"
    else:
        xcom = "Xcom-LAN"
    
    xcom_context = f"\n==={datetime_posix}===\n{xcom} version: {xcom_version}\n - Xt present: {fst_bits[5]}\n - BSP present: {fst_bits[6]}\n - Vt present: {fst_bits[7]}\n - VS present: {snd_bits[0]}"

    return xcom_context


# Calculate the checksum for the given data and length
def calc_checksum(data, length):
    
    """Calculate the checksum for the given data and length"""

    if debug : print(" --- calc_checksum")    

    try:
        A = 0xFF
        B = 0
        # For each byte, it updates the variables A and B by performing bitwise operations. 
        # It returns a value obtained by shifting the bits of A by 8 positions to the left 
        # and performing a bitwise OR operation with B.
        for i in range(0, length, 2):
            value = data[i] + data[i + 1]
            A = (A + int(value, 16)) & 0xFF
            B = (B + A) & 0xFF

        return (A << 8) | B
    except ValueError as e:
        print(e.message if hasattr(e, 'message') else e)
        exit()
    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        exit()


# Convert a float value to a HEX code
def convert_float_to_hex(float_value):
    
    """Convert a float value to a HEX code"""

    if debug : print("   --- convert_float_to_hex")

    try:
        binary = struct.pack('<f', float_value)
        return binary.hex().zfill(8)
    except ValueError as e:
        print(e.message if hasattr(e, 'message') else e)
        exit()
    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        exit()


# Convert a int value to a HEX code
def convert_int32_to_hex(int_value, byte_length):
    
    """Convert a int value to a HEX code"""

    if debug : print("   --- convert_int32_to_hex")

    try:
        return int_value.to_bytes(byte_length, byteorder='little').hex()
    except ValueError as e:
        print(e.message if hasattr(e, 'message') else e)
        exit()
    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        exit()


# Convert a boolean value to a HEX code
def convert_bool_to_hex(bool_value):
    
    """Convert a boolean value to a HEX code"""

    if debug : print("   --- convert_bool_to_hex")

    try:
        binary = struct.pack('<?', bool_value)
        return binary.hex()    
    except ValueError as e:
        print(e.message if hasattr(e, 'message') else e)
        exit()
    except Exception as e:
        print(e.message if hasattr(e, 'message') else e)
        exit()


# Convert a value to a specified format
def convert_to_hex_from_format(data, format):
    
    """Convert a value to a specified format"""

    if debug : print("   --- convert_to_hex_from_format")

    if format.lower() == "bool":
        data = int(data)
        return convert_bool_to_hex(data)
    elif format.lower() == "short_enum":
        data = int(data)
        return convert_int32_to_hex(data, 2)
    elif format.lower() == "long_enum":
        data = int(data)
        return convert_int32_to_hex(data, 4)
    elif format.lower() == "float":
        data = float(data)        
        return convert_float_to_hex(data)
    elif format.lower() == "int32":
        data = int(data)
        return convert_int32_to_hex(data, 4)
    

# Get the given assembly's id
def convert_assembly_to_id(assembly):
    
    """Get the given assembly's id"""

    if debug : print("   --- convert_assembly_to_id")

    if assembly.lower() == "average":
        return 253
    elif assembly.lower() == "sum":
        return 254
    elif assembly.lower() == "master":
        return 0
    else:
        for i in range(1, 16):
            if assembly.lower() == f"uid{i}":
                return i 


# Get the given assembly's id
def convert_id_to_assembly(id):
    
    """Get the given assembly's id"""

    if debug : print("   --- convert_id_to_assembly")

    if id == 253:
        return "Average"
    elif id == 254:
        return "Sum"
    elif id == 0:
        return "Master"
    else:
        return f"Uid{id}"


# Check if the given frame use the "read_property" service
def is_txFrame_read(tx_frame):
    
    """Check if the given frame use the "read_property" service"""

    if debug : print(" --- is_txframe_read")

    service_id = tx_frame[30:32]
    if service_id == "01":
        return True
    elif service_id == "02":
        return False


# Check if the given format is usable
def check_format(format_string):
    
    """Check if the given format is usable"""

    if debug : print(" --- check_format") 

    formats = ["bool", "format", "enum", "short_enum", "long_enum", "error", "int32", "float", "string", "dynamic", "byte_stream"]
    if format_string.lower() in formats:
        return True
    return False


# Check if the given frame has an error
def check_frame_has_error(frame):    
    
    """Check if the given frame has an error"""

    if debug : print(" --- check_frame_has_error")

    service_flags = frame[28:30]
    # If the frame has an error, the "service_flags" will always be "03"
    if service_flags == "03":
        return True
    elif service_flags == "02":
        return False
    

# Check if the given port with the given baudrate can be opened
def can_open_port(name, baudrate):
    # Check if the given port with the given baudrate can be opened
    """Check if the given frame has an error"""

    if debug : print(" --- can_open_port")

    try:
        serial.serial_for_url(url=name, baudrate=baudrate, timeout=3, write_timeout=3, bytesize=8, parity=serial.PARITY_EVEN, stopbits=1)
        return True
    except:
        return False


# Execute commands methode when executing this script
if __name__ == '__main__':
    commands()
    

