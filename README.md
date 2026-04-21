/* Operation Codes */

PTP_OC_Undefined                0x1000
PTP_OC_GetDeviceInfo            0x1001
PTP_OC_OpenSession              0x1002
PTP_OC_CloseSession             0x1003
PTP_OC_GetStorageIDs            0x1004
PTP_OC_GetStorageInfo           0x1005
PTP_OC_GetNumObjects            0x1006
PTP_OC_GetObjectHandles         0x1007
PTP_OC_GetObjectInfo            0x1008
PTP_OC_GetObject                0x1009
PTP_OC_GetThumb                 0x100A
PTP_OC_DeleteObject             0x100B
PTP_OC_SendObjectInfo           0x100C
PTP_OC_SendObject               0x100D
PTP_OC_InitiateCapture          0x100E
PTP_OC_FormatStore              0x100F
PTP_OC_ResetDevice              0x1010
PTP_OC_SelfTest                 0x1011
PTP_OC_SetObjectProtection      0x1012
PTP_OC_PowerDown                0x1013
PTP_OC_GetDevicePropDesc        0x1014
PTP_OC_GetDevicePropValue       0x1015
PTP_OC_SetDevicePropValue       0x1016
PTP_OC_ResetDevicePropValue     0x1017
PTP_OC_TerminateOpenCapture     0x1018
PTP_OC_MoveObject               0x1019
PTP_OC_CopyObject               0x101A
PTP_OC_GetPartialObject         0x101B
PTP_OC_InitiateOpenCapture      0x101C
/* Eastman Kodak extension Operation Codes */
PTP_OC_EK_SendFileObjectInfo	0x9005
PTP_OC_EK_SendFileObject	0x9006
<br>
<br>
<br>
/* PTP Storage Types */
#define PTP_ST_Undefined			0x0000
#define PTP_ST_FixedROM				0x0001
#define PTP_ST_RemovableROM			0x0002
#define PTP_ST_FixedRAM				0x0003
#define PTP_ST_RemovableRAM			0x0004
<br>
<br>
<br>
/* PTP FilesystemType Values */
#define PTP_FST_Undefined			0x0000
#define PTP_FST_GenericFlat			0x0001
#define PTP_FST_GenericHierarchical		0x0002
#define PTP_FST_DCF				0x0003
<br>
<br>
<br>
/* PTP StorageInfo AccessCapability Values */
#define PTP_AC_ReadWrite			0x0000
#define PTP_AC_ReadOnly				0x0001
#define PTP_AC_ReadOnly_with_Object_Deletion	0x0002