using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using UnityEditor.AssetImporters;
using UnityEngine;

using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEngine.Rendering;

public class FmtAttribute
{
    public string type;
    public int count;
}

public class FmtHeader
{
    public int verticesCount;
    public int IndicesCount;
    public string topology;
    public Dictionary<string, FmtAttribute> attributes;
}

public class FmtData
{
    public List<Dictionary<string, object>> vertices;
    public List<int> indices;
}

public class FmtMesh
{
    public FmtHeader header;
    public FmtData data;
}


[ScriptedImporter(1, "fmt")]
public class FmtImporter : ScriptedImporter
{
    private static readonly Dictionary<string, VertexAttribute> AttributeMapping = new()
    {
        {"POSITION", VertexAttribute.Position},
        {"TEXCOORD0", VertexAttribute.TexCoord0},
        {"TEXCOORD1", VertexAttribute.TexCoord1},
    };

    private static readonly Dictionary<string, VertexAttributeFormat> FormatMapping = new()
    {
        {"float32", VertexAttributeFormat.Float32},
        {"int32", VertexAttributeFormat.SInt32},
        {"uint8", VertexAttributeFormat.UInt8},
    };
    
    private static readonly Dictionary<string, Type> TypeMapping = new()
    {
        {"float32", typeof(float)},
        {"int32", typeof(int)},
        {"uint8", typeof(byte)},
    };
    
    private static readonly Dictionary<string, int> SizeMapping = new()
    {
        {"float32", 4},
        {"int32", 4},
        {"uint8", 1},
    };
    
    private static readonly Dictionary<string, MeshTopology> TopologyMapping = new()
    {
        {"EDGE", MeshTopology.Lines},
        {"TRIANGLE", MeshTopology.Triangles}
    };

    private byte[] ObjectToBytes(object o, Type t, int count)
    {
        if (count > 1)
        {
            using (MemoryStream memStream = new MemoryStream(12))
            {
                foreach (var o2 in (IEnumerable)o)
                    memStream.Write(ObjectToBytes(o2, t, 1));
                return memStream.ToArray();
            }
        }

        if (o is JValue)
            o = ((JValue)o).Value!;

        if (t == typeof(float))
        {
            if (o is double)
                o = Convert.ToSingle((double)o);
            return BitConverter.GetBytes((float)o);
        }

        if (o is long)
            o = Convert.ToInt32((long)o);
        
        if (t == typeof(int))
            return BitConverter.GetBytes((int)o);
        if (t == typeof(byte))
            return new[] {Convert.ToByte((int)o)};

        throw new ArgumentException("Invalid type");
    }

    private byte[] VertexToBytes(Dictionary<string, object> vertex, int vertexSize, Dictionary<string, FmtAttribute> attributes)
    {
        using (MemoryStream memStream = new MemoryStream(vertexSize))
        {
            foreach (var attr in attributes)
            {
                var bytes = ObjectToBytes(vertex[attr.Key], TypeMapping[attr.Value.type], attr.Value.count);
                memStream.Write(bytes);
            }

            if (memStream.Length != vertexSize)
                throw new Exception($"Vertex size error: {memStream.Length}/{vertexSize}");
            return memStream.ToArray();
        }
    }
    struct Struct16 { public int _4, _8, _12, _16; }
    struct Struct20 { public int _4, _8, _12, _16, _20; }

    T[] ConvertByteToStructArray<T>(byte[] data, int size, int count) where T : struct
    {
        T[] dataStruct = new T[count];
        for (int i = 0; i < count; i++)
        {
            IntPtr ptPoit = Marshal.AllocHGlobal(size);
            Marshal.Copy(data, i * size, ptPoit, size);
            dataStruct[i] = (T) Marshal.PtrToStructure(ptPoit, typeof (T));
            Marshal.FreeHGlobal(ptPoit);
        }
        return dataStruct;
    }
    
    void SetVertexBufferData(Mesh mesh, byte[] verticesData, int size, int count)
    {
        switch (size)
        {
            case 16: mesh.SetVertexBufferData(ConvertByteToStructArray<Struct16>(verticesData, size, count), 0, 0, count); break;
            case 20: mesh.SetVertexBufferData(ConvertByteToStructArray<Struct20>(verticesData, size, count), 0, 0, count); break;
        }
    }
    
    public override void OnImportAsset(AssetImportContext ctx)
    {
        var fmtMesh = JsonConvert.DeserializeObject<FmtMesh>(File.ReadAllText(ctx.assetPath));
        if (fmtMesh == null)
        {
            Debug.LogError("JsonConvert failed to parse .fmt file");
            return;
        }
        
        // Init vertex layout
        var layout = new List<VertexAttributeDescriptor>();
        int vertexSize = 0;
        foreach (var attr in fmtMesh.header.attributes)
        {
            layout.Add(new VertexAttributeDescriptor(AttributeMapping[attr.Key], FormatMapping[attr.Value.type], attr.Value.count));
            vertexSize += SizeMapping[attr.Value.type] * attr.Value.count;
        }

        // init vertex buffer
        int verticesCount = fmtMesh.header.verticesCount;
        byte[] vertices;
        using (MemoryStream memStream = new MemoryStream(vertexSize * verticesCount))
        {
            foreach (var vertex in fmtMesh.data.vertices)
                memStream.Write(VertexToBytes(vertex, vertexSize, fmtMesh.header.attributes));
            vertices = memStream.ToArray();
        }

        var mesh = new Mesh();
        mesh.SetVertexBufferParams(fmtMesh.header.verticesCount, layout.ToArray());
        SetVertexBufferData(mesh, vertices, vertexSize, verticesCount);
        mesh.SetIndexBufferParams(fmtMesh.header.IndicesCount, IndexFormat.UInt32);
        mesh.SetIndexBufferData(fmtMesh.data.indices,0 , 0, fmtMesh.header.IndicesCount);
        mesh.subMeshCount = 1;
        mesh.SetSubMesh(0, new SubMeshDescriptor(0, fmtMesh.header.IndicesCount, TopologyMapping[fmtMesh.header.topology]));
        mesh.RecalculateBounds();
        
        ctx.AddObjectToAsset("mesh", mesh);
        ctx.SetMainObject(mesh);
    }
}