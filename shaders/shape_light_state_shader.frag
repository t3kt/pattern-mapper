#define PATH_MODE

#include "shape_shader_pixel_common"

/*
r: light index (global), aka the sample
   to use when grabbing values from a chop
   with a sample for each light
g: segment index, aka the x coord in the map
b: shape index
a: vertex
*/
#define sLightMap sTD2DInputs[0]

#define sColors sTD2DInputs[1]
#define uColorsInfo uTD2DInfos[1]

#define sAttrs sTD2DInputs[3]

#define sTexParams sTD2DInputs[2]
#define sTexture1 sTD2DInputs[4]
#define sTexture2 sTD2DInputs[5]

/*
    row:
        r/g/b: tx/y/z
    row:
        r/g/b: pathu/v/w
    row:
        r/g/b: faceu/v/w
    row:
        r/g/b: globalu/v/w
*/
#define sLightCoords sTD2DInputs[6]

uniform int uLightCount;

void loadLightAttrs(inout VertexAttrs attrs, int lightIndex, int shapeIndex) {
}

out vec4 fragColor;
void main() {
//    vec4 lightMapVals = texelFetch(sLightMap, ivec2(vUV.st * uTD2DInfos[0].res.zw), 0);
    vec4 lightMapVals = texture(sLightMap, vUV.st);
    int lightIndex = int(lightMapVals.r);
    int segIndex = int(lightMapVals.g);
    int shapeIndex = int(lightMapVals.b);
    float vertex = lightMapVals.a;
    VertexAttrs attrs;
    attrs.worldSpacePos = texelFetch(sLightCoords, ivec2(lightIndex, 0), 0).xyz;
    attrs.pathTexCoord = texelFetch(sLightCoords, ivec2(lightIndex, 1), 0).xy;
    attrs.faceTexCoord = texelFetch(sLightCoords, ivec2(lightIndex, 2), 0).xyz;
    attrs.globalTexCoord = texelFetch(sLightCoords, ivec2(lightIndex, 3), 0).xyz;
    attrs.color = texelFetch(sColors, ivec2(shapeIndex, 0), 0);

    // This must happen after because it depends on/modifies the uvs
    loadBasicVertexAttrs(attrs, shapeIndex, sTexParams, sColors, sAttrs);

    vec4 color;
    if (lightIndex < 0) {
        color = vec4(0);
    } else {
        color = attrs.color;
//        color = texelFetch(sColors, ivec2(shapeIndex, 0), 0);
//        color = vec4(uColorsInfo.res.z);
//        color = vec4(shapeIndex);
//        color = vec4(vec2(vUV.st * uTD2DInfos[0].res.zw), 0, 1);
//        color = texture(sColors, vec2(float(shapeIndex) / (uColorsInfo.res.z - 1.0), 0));
		applyTexture(color, attrs, attrs.pathTex, sTexture1, sTexture2);
//        color = lightMapVals;
//        color = vec4(attrs.globalTexCoord, 1);
    }
    fragColor = TDOutputSwizzle(color);
}
