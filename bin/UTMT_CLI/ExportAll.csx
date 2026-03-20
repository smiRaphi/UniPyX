using System.Text;
using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Linq;
using UndertaleModLib.Util;

string output = ".";

EnsureDataLoaded();

if (!Data.IsYYC())
{
    GlobalDecompileContext globalDecompileContext = new(Data);
    Underanalyzer.Decompiler.IDecompileSettings decompilerSettings = Data.ToolInfo.DecompilerSettings;
    List<UndertaleCode> toDump = Data.Code.Where(c => c.ParentEntry is null).ToList();
    string codeFolder = Path.Combine(output,"Code");
    if (toDump.Count > 0 && !Directory.Exists(codeFolder)) Directory.CreateDirectory(codeFolder);
    await DumpCodes();

    async Task DumpCodes()
    {
        await Task.Run(() => Parallel.ForEach(toDump, DumpCode));
    }
    void DumpCode(UndertaleCode code)
    {
        if (code is not null)
        {
            string path = Path.Combine(codeFolder, code.Name.Content + ".gml");
            try
            {
                File.WriteAllText(path, (code != null 
                    ? new Underanalyzer.Decompiler.DecompileContext(globalDecompileContext, code, decompilerSettings).DecompileToString() 
                    : ""));
            }
            catch (Exception e)
            {
                File.WriteAllText(path, "/*\nDECOMPILER FAILED!\n\n" + e.ToString() + "\n*/");
            }
        }
    }
}

string texturesFolder = Path.Combine(output,"Textures");
if (Data.EmbeddedTextures.Count > 0 && !Directory.Exists(texturesFolder)) Directory.CreateDirectory(texturesFolder);
await Task.Run(() =>
{
    for (int i = 0; i < Data.EmbeddedTextures.Count; i++)
    {
        try
        {
            using FileStream fs = new(Path.Combine(texturesFolder, $"{i}.png"), FileMode.Create);
            Data.EmbeddedTextures[i].TextureData.Image.SavePng(fs);
        }
        catch (Exception ex) {}
    }
});

string fntFolder = Path.Combine(output,"Fonts");
if (Data.Fonts.Count > 0 && !Directory.Exists(fntFolder)) Directory.CreateDirectory(fntFolder);
TextureWorker worker1 = null;
using (worker1 = new())
{
    await DumpFonts();
}
async Task DumpFonts()
{
    await Task.Run(() => Parallel.ForEach(Data.Fonts, DumpFont));
}
void DumpFont(UndertaleFont font)
{
    if (font is not null)
    {
        worker1.ExportAsPNG(font.Texture, Path.Combine(fntFolder, $"{font.Name.Content}.png"));
        using (StreamWriter writer = new(Path.Combine(fntFolder, $"glyphs_{font.Name.Content}.csv")))
        {
            writer.WriteLine($"{font.DisplayName};{font.EmSize};{font.Bold};{font.Italic};{font.Charset};{font.AntiAliasing};{font.ScaleX};{font.ScaleY}");

            foreach (var g in font.Glyphs)
            {
                writer.WriteLine($"{g.Character};{g.SourceX};{g.SourceY};{g.SourceWidth};{g.SourceHeight};{g.Shift};{g.Offset}");
            }
        }
    }
}

string maskFolder = Path.Combine(output,"Masks");
TextureWorker worker2 = null;
using (worker2 = new())
{
    await DumpMasks();
}
async Task DumpMasks()
{
    await Task.Run(() => Parallel.ForEach(Data.Sprites, DumpMask));
}
void DumpMask(UndertaleSprite sprite)
{
    if (sprite is null)
    {
        return;
    }

    for (int i = 0; i < sprite.CollisionMasks.Count; i++)
    {
        if (sprite.CollisionMasks[i]?.Data is not null)
        {
            (int maskWidth, int maskHeight) = sprite.CalculateMaskDimensions(Data);
            if (!Directory.Exists(maskFolder)) Directory.CreateDirectory(maskFolder);
            TextureWorker.ExportCollisionMaskPNG(sprite.CollisionMasks[i], Path.Combine(maskFolder, $"{sprite.Name.Content}_{i}.png"), maskWidth, maskHeight);
        }
    }
}

string shaderFolder = Path.Combine(output,"Shaders");
foreach (UndertaleShader shader in Data.Shaders)
{
    if (shader is null)
    {
        continue;
    }

    string exportBase = Path.Combine(shaderFolder, shader.Name.Content);
    Directory.CreateDirectory(exportBase);

    File.WriteAllText(Path.Combine(exportBase, "Type.txt"), shader.Type.ToString());
    File.WriteAllText(Path.Combine(exportBase, "GLSL_ES_Fragment.txt"), shader.GLSL_ES_Fragment.Content);
    File.WriteAllText(Path.Combine(exportBase, "GLSL_ES_Vertex.txt"), shader.GLSL_ES_Vertex.Content);
    File.WriteAllText(Path.Combine(exportBase, "GLSL_Fragment.txt"), shader.GLSL_Fragment.Content);
    File.WriteAllText(Path.Combine(exportBase, "GLSL_Vertex.txt"), shader.GLSL_Vertex.Content);
    File.WriteAllText(Path.Combine(exportBase, "HLSL9_Fragment.txt"), shader.HLSL9_Fragment.Content);
    File.WriteAllText(Path.Combine(exportBase, "HLSL9_Vertex.txt"), shader.HLSL9_Vertex.Content);
    if (!shader.HLSL11_VertexData.IsNull)
        File.WriteAllBytes(Path.Combine(exportBase, "HLSL11_VertexData.bin"), shader.HLSL11_VertexData.Data);
    if (!shader.HLSL11_PixelData.IsNull)
        File.WriteAllBytes(Path.Combine(exportBase, "HLSL11_PixelData.bin"), shader.HLSL11_PixelData.Data);
    if (!shader.PSSL_VertexData.IsNull)
        File.WriteAllBytes(Path.Combine(exportBase, "PSSL_VertexData.bin"), shader.PSSL_VertexData.Data);
    if (!shader.PSSL_PixelData.IsNull)
        File.WriteAllBytes(Path.Combine(exportBase, "PSSL_PixelData.bin"), shader.PSSL_PixelData.Data);
    if (!shader.Cg_PSVita_VertexData.IsNull)
        File.WriteAllBytes(Path.Combine(exportBase, "Cg_PSVita_VertexData.bin"), shader.Cg_PSVita_VertexData.Data);
    if (!shader.Cg_PSVita_PixelData.IsNull)
        File.WriteAllBytes(Path.Combine(exportBase, "Cg_PSVita_PixelData.bin"), shader.Cg_PSVita_PixelData.Data);
    if (!shader.Cg_PS3_VertexData.IsNull)
        File.WriteAllBytes(Path.Combine(exportBase, "Cg_PS3_VertexData.bin"), shader.Cg_PS3_VertexData.Data);
    if (!shader.Cg_PS3_PixelData.IsNull)
        File.WriteAllBytes(Path.Combine(exportBase, "Cg_PS3_PixelData.bin"), shader.Cg_PS3_PixelData.Data);

    StringBuilder vertexSb = new();
    for (var i = 0; i < shader.VertexShaderAttributes.Count; i++)
    {
        vertexSb.AppendLine(shader.VertexShaderAttributes[i].Name.Content);
    }
    File.WriteAllText(Path.Combine(exportBase, "VertexShaderAttributes.txt"), vertexSb.ToString());
}

string soundFolder = Path.Combine(output,"Sounds");
bool copyExternalAudio = false;
bool groupedExport = (Data.AudioGroups?.Count ?? 0) > 0;
byte[] EMPTY_WAV_FILE_BYTES = System.Convert.FromBase64String("UklGRiQAAABXQVZFZm10IBAAAAABAAIAQB8AAAB9AAAEABAAZGF0YQAAAAA=");
string DEFAULT_AUDIOGROUP_NAME = "audiogroup_default";
await Task.Run(DumpSounds);
Dictionary<string, IList<UndertaleEmbeddedAudio>> loadedAudioGroups = null;
IList<UndertaleEmbeddedAudio> GetAudioGroupData(UndertaleSound sound)
{
    loadedAudioGroups ??= new();

    // Try getting cached audio group by name.
    string audioGroupName = sound.AudioGroup is not null ? sound.AudioGroup.Name.Content : DEFAULT_AUDIOGROUP_NAME;
    if (loadedAudioGroups.ContainsKey(audioGroupName))
    {
        return loadedAudioGroups[audioGroupName];
    }

    // Not cached, so try locating audiogroup file.
    string relativeAudioGroupPath;
    if (sound.AudioGroup is UndertaleAudioGroup { Path.Content: string customRelativePath })
    {
        relativeAudioGroupPath = customRelativePath;
    }
    else
    {
        relativeAudioGroupPath = $"audiogroup{sound.GroupID}.dat";
    }
    string groupFilePath = Path.Combine(Path.GetDirectoryName(FilePath), relativeAudioGroupPath);
    if (!File.Exists(groupFilePath))
    {
        // Doesn't exist... don't try loading.
        return null;
    }

    // Load data file.
    try
    {
        UndertaleData data = null;
        using (var stream = new FileStream(groupFilePath, FileMode.Open, FileAccess.Read))
        {
            data = UndertaleIO.Read(stream, (warning, _) => ScriptWarning($"A warning occured while trying to load {audioGroupName}:\n{warning}"));
        }

        loadedAudioGroups[audioGroupName] = data.EmbeddedAudio;
        return data.EmbeddedAudio;
    } 
    catch (Exception e)
    {
        ScriptError($"An error occured while trying to load {audioGroupName}:\n{e.Message}");
        return null;
    }
}
byte[] GetSoundData(UndertaleSound sound)
{
    // Try to get audio directly, if embedded in main file.
    if (sound.AudioFile is not null)
    {
        return sound.AudioFile.Data;
    }

    // Try to get audio from its audiogroup.
    if (sound.GroupID > Data.GetBuiltinSoundGroupID())
    {
        IList<UndertaleEmbeddedAudio> audioGroup = GetAudioGroupData(sound);
        if (audioGroup is not null)
        {
            return audioGroup[sound.AudioID].Data;
        }
    }

    // All attempts to get data failed; just use empty WAV data.
    return EMPTY_WAV_FILE_BYTES;
}
void DumpSounds()
{
    foreach (UndertaleSound sound in Data.Sounds)
    {
        if (sound is not null)
        {
            DumpSound(sound);
        }
    }
}
void DumpSound(UndertaleSound sound)
{
    // Determine output audio file path.
    string soundName = sound.Name.Content;
    string soundFilePath;
    if (groupedExport)
    {
        soundFilePath = Path.Combine(soundFolder, sound.AudioGroup.Name.Content, soundName);
        Directory.CreateDirectory(Path.Combine(soundFolder, sound.AudioGroup.Name.Content));
    }
    else
    {
        soundFilePath = Path.Combine(soundFolder, soundName);
    }

    // Determine output file type.
    bool flagCompressed = sound.Flags.HasFlag(UndertaleSound.AudioEntryFlags.IsCompressed);
    bool flagEmbedded = sound.Flags.HasFlag(UndertaleSound.AudioEntryFlags.IsEmbedded);
    string audioExt = ".ogg";
    bool isEmbedded = true;
    if (flagEmbedded && !flagCompressed)
    {
        // IsEmbedded, Regular: WAV, embedded.
        audioExt = ".wav";
    }
    else if (flagCompressed && !flagEmbedded)
    {
        // IsCompressed, Regular: OGG, embedded.
        audioExt = ".ogg";
    }
    else if (flagCompressed && flagEmbedded)
    {
        // IsEmbedded, IsCompressed, Regular: OGG, embedded.
        audioExt = ".ogg";
    }
    else if (!flagCompressed && !flagEmbedded)
    {
        // Regular: OGG, external.
        isEmbedded = false;
        audioExt = ".ogg";

        // Only copy external audio if enabled.
        if (copyExternalAudio)
        {
            string externalFilename = sound.File.Content;
            if (!externalFilename.Contains('.'))
            {
                // Add file extension if none already exists (assume OGG).
                externalFilename += ".ogg";
            }
            string sourcePath = Path.Combine(Path.GetDirectoryName(FilePath), externalFilename);
            string destPath;
            if (groupedExport)
            {
                destPath = Path.Combine(soundFolder, sound.AudioGroup.Name.Content, "external", soundName + audioExt);
                Directory.CreateDirectory(Path.Combine(soundFolder, sound.AudioGroup.Name.Content, "external"));
            }
            else
            {
                destPath = Path.Combine(soundFolder, "external", soundName + audioExt);
                Directory.CreateDirectory(Path.Combine(soundFolder, "external"));
            }
            File.Copy(sourcePath, destPath, true);
        }
    }
    if (isEmbedded)
    {
        File.WriteAllBytes(soundFilePath + audioExt, GetSoundData(sound));
    }
}

string sprFolder = Path.Combine(output, "Sprites");
if (Data.Sprites.Count > 0 && !Directory.Exists(sprFolder)) Directory.CreateDirectory(sprFolder);
bool padded = false;
bool useSubDirectories = false;
TextureWorker worker3 = null;
using (worker3 = new())
{
    await DumpSprites();
}
async Task DumpSprites()
{
    await Task.Run(() => Parallel.ForEach(Data.Sprites, DumpSprite));
}
void DumpSprite(UndertaleSprite sprite)
{
    if (sprite is not null)
    {
        string outputFolder = sprFolder;
        if (useSubDirectories)
        {
            outputFolder = Path.Combine(outputFolder, sprite.Name.Content);
            if (sprite.Textures.Count > 0)
            {
                Directory.CreateDirectory(outputFolder);
            }
        }
            
        for (int i = 0; i < sprite.Textures.Count; i++)
        {
            if (sprite.Textures[i]?.Texture is not null)
            {
                worker3.ExportAsPNG(sprite.Textures[i].Texture, Path.Combine(outputFolder, $"{sprite.Name.Content}_{i}.png"), null, padded);
            }
        }
    }
}

if (Data.Strings.Count > 0)
{
    string stringsPath = Path.Combine(output, "Strings.txt");
    bool promptedForNewlines = false;
    bool skipNewlines = false;
    using (StreamWriter writer = new StreamWriter(stringsPath))
    {
        foreach (var str in Data.Strings)
        {
            if (str.Content.Contains('\n') || str.Content.Contains('\r'))
            {
                if (!promptedForNewlines)
                {
                    promptedForNewlines = true;
                    skipNewlines = ScriptQuestion("Export strings containing newlines? Doing so will break reimporting.");
                }
                if (skipNewlines)
                {
                    continue;
                }
            }
            writer.WriteLine(str.Content);
        }
    }
}

string bgrFolder = Path.Combine(output, "Backgrounds");
if (Data.Backgrounds.Count > 0 && !Directory.Exists(bgrFolder)) Directory.CreateDirectory(bgrFolder);
TextureWorker worker4 = null;
using (worker4 = new())
{
    await DumpBackgrounds();
}
async Task DumpBackgrounds()
{
    await Task.Run(() => Parallel.ForEach(Data.Backgrounds, DumpBackground));
}
void DumpBackground(UndertaleBackground background)
{
    if (background?.Texture is null)
    {
        return;
    }

    UndertaleTexturePageItem tex = background.Texture;
    worker4.ExportAsPNG(tex, Path.Combine(bgrFolder, $"{background.Name.Content}.png"));
}
